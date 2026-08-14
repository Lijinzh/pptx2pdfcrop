from __future__ import annotations

import gc
import os
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from .errors import BackendUnavailableError, Pptx2PdfCropError
from .pages import resolve_slides

PP_SAVE_AS_OPEN_XML_PRESENTATION = 24
PP_FIXED_FORMAT_TYPE_PDF = 2
PP_FIXED_FORMAT_INTENT_PRINT = 2
PP_PRINT_HANDOUT_VERTICAL_FIRST = 1
PP_PRINT_OUTPUT_SLIDES = 1
PP_PRINT_ALL = 1
PP_ALERTS_NONE = 1

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class PresentationInfo:
    slide_count: int
    width_points: float
    height_points: float
    powerpoint_version: str


def friendly_powerpoint_errors(operation: str):
    """Convert pywin32 COM failures into concise, actionable CLI errors."""

    def decorator(function: Any):
        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return function(*args, **kwargs)
            except Pptx2PdfCropError:
                raise
            except Exception as exc:
                raise Pptx2PdfCropError(f"{operation} failed: {exc}") from exc

        return wrapped

    return decorator


def _load_win32() -> tuple[Any, Any]:
    if os.name != "nt":
        raise BackendUnavailableError("pptx2pdfcrop supports Windows only.")
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise BackendUnavailableError(
            "pywin32 is missing. Reinstall with `uv tool install pptx2pdfcrop`."
        ) from exc
    return pythoncom, win32com.client


@contextmanager
def powerpoint_application() -> Iterator[Any]:
    """Start a private hidden PowerPoint COM instance and always close it."""

    pythoncom, win32_client = _load_win32()
    pythoncom.CoInitialize()
    application = None
    try:
        application = win32_client.DispatchEx("PowerPoint.Application")
        application.DisplayAlerts = PP_ALERTS_NONE
    except Exception as exc:
        raise BackendUnavailableError(
            "Microsoft PowerPoint automation could not start. Confirm that desktop PowerPoint "
            "is installed."
        ) from exc
    try:
        yield application
    finally:
        if application is not None:
            with suppress(Exception):
                application.Quit()
        application = None
        gc.collect()
        pythoncom.CoUninitialize()


@friendly_powerpoint_errors("PowerPoint presentation inspection")
def inspect_presentation(source: Path) -> PresentationInfo:
    presentation = None
    with powerpoint_application() as application:
        try:
            presentation = application.Presentations.Open(
                str(source.resolve()),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )
            return PresentationInfo(
                slide_count=int(presentation.Slides.Count),
                width_points=float(presentation.PageSetup.SlideWidth),
                height_points=float(presentation.PageSetup.SlideHeight),
                powerpoint_version=str(application.Version),
            )
        finally:
            if presentation is not None:
                presentation.Close()


@friendly_powerpoint_errors("PowerPoint TIFF export")
def export_slides_to_tiff(
    source: Path,
    output_dir: Path,
    *,
    slides: list[int] | None,
    dpi: int,
) -> tuple[list[Path], PresentationInfo, list[int]]:
    """Rasterize slides inside PowerPoint so transparency is flattened by PowerPoint itself."""

    presentation = None
    outputs: list[Path] = []
    with powerpoint_application() as application:
        try:
            presentation = application.Presentations.Open(
                str(source.resolve()),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )
            info = PresentationInfo(
                slide_count=int(presentation.Slides.Count),
                width_points=float(presentation.PageSetup.SlideWidth),
                height_points=float(presentation.PageSetup.SlideHeight),
                powerpoint_version=str(application.Version),
            )
            resolved = resolve_slides(slides, info.slide_count)
            width_pixels = round(info.width_points / 72.0 * dpi)
            height_pixels = round(info.height_points / 72.0 * dpi)

            for sequence, slide_number in enumerate(resolved, start=1):
                output = output_dir / f"raw-{sequence:04d}-slide-{slide_number}.tif"
                presentation.Slides.Item(slide_number).Export(
                    str(output),
                    "TIF",
                    width_pixels,
                    height_pixels,
                )
                if not output.is_file() or output.stat().st_size == 0:
                    raise Pptx2PdfCropError(
                        f"PowerPoint did not create the TIFF for slide {slide_number}."
                    )
                outputs.append(output)
            return outputs, info, resolved
        finally:
            if presentation is not None:
                presentation.Close()


@friendly_powerpoint_errors("PowerPoint vector PDF export")
def export_slides_to_vector_pdf(
    source: Path,
    output_pdf: Path,
    working_copy: Path,
    *,
    slides: list[int] | None,
) -> tuple[PresentationInfo, list[int]]:
    """Export selected slide indexes to a native PowerPoint PDF.

    A temporary copy is trimmed first instead of using PowerPoint print page numbers, because
    custom first-slide numbering can otherwise export the wrong slide.
    """

    source_presentation = None
    working_presentation = None
    dummy_range = None
    with powerpoint_application() as application:
        try:
            source_presentation = application.Presentations.Open(
                str(source.resolve()),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )
            info = PresentationInfo(
                slide_count=int(source_presentation.Slides.Count),
                width_points=float(source_presentation.PageSetup.SlideWidth),
                height_points=float(source_presentation.PageSetup.SlideHeight),
                powerpoint_version=str(application.Version),
            )
            resolved = resolve_slides(slides, info.slide_count)
            source_presentation.SaveCopyAs(
                str(working_copy),
                PP_SAVE_AS_OPEN_XML_PRESENTATION,
            )
            source_presentation.Close()
            source_presentation = None

            working_presentation = application.Presentations.Open(
                str(working_copy),
                ReadOnly=False,
                Untitled=False,
                WithWindow=False,
            )
            selected = set(resolved)
            for slide_number in range(info.slide_count, 0, -1):
                if slide_number not in selected:
                    working_presentation.Slides.Item(slide_number).Delete()

            working_presentation.PrintOptions.Ranges.ClearAll()
            dummy_range = working_presentation.PrintOptions.Ranges.Add(1, 1)
            working_presentation.ExportAsFixedFormat(
                str(output_pdf),
                PP_FIXED_FORMAT_TYPE_PDF,
                PP_FIXED_FORMAT_INTENT_PRINT,
                0,
                PP_PRINT_HANDOUT_VERTICAL_FIRST,
                PP_PRINT_OUTPUT_SLIDES,
                0,
                dummy_range,
                PP_PRINT_ALL,
                "",
                True,
                True,
                True,
                True,
                False,
            )
            if not output_pdf.is_file() or output_pdf.stat().st_size == 0:
                raise Pptx2PdfCropError("PowerPoint did not create the vector PDF.")
            return info, resolved
        finally:
            dummy_range = None
            if working_presentation is not None:
                working_presentation.Saved = True
                working_presentation.Close()
            if source_presentation is not None:
                source_presentation.Close()


def probe_powerpoint() -> tuple[bool, str]:
    try:
        with powerpoint_application() as application:
            return True, str(application.Version)
    except BackendUnavailableError as exc:
        return False, str(exc)
