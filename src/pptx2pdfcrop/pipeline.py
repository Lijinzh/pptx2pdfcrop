from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .errors import Pptx2PdfCropError
from .models import ExportOptions, ExportResult, Mode
from .pages import compact_slide_label, parse_slide_spec
from .powerpoint import export_slides_to_tiff, export_slides_to_vector_pdf
from .raster_pdf import crop_and_encode_images, images_to_pdf
from .vector_pdf import crop_vector_pdf


def _validate_options(options: ExportOptions) -> None:
    if os.name != "nt":
        raise Pptx2PdfCropError("pptx2pdfcrop currently supports Windows only.")
    if not options.source.is_file():
        raise Pptx2PdfCropError(f"Input presentation not found: {options.source}")
    if options.source.suffix.lower() not in {".ppt", ".pptx", ".pptm", ".ppsx"}:
        raise Pptx2PdfCropError("Input must be a PowerPoint presentation.")
    if not 150 <= options.dpi <= 1200:
        raise Pptx2PdfCropError("--dpi must be between 150 and 1200.")
    if options.crop_dpi < 72:
        raise Pptx2PdfCropError("--crop-dpi must be at least 72.")
    if not 80 <= options.jpeg_quality <= 100:
        raise Pptx2PdfCropError("--jpeg-quality must be between 80 and 100.")
    if not 1 <= options.white_threshold <= 255:
        raise Pptx2PdfCropError("--white-threshold must be between 1 and 255.")
    if options.padding_points < 0:
        raise Pptx2PdfCropError("--padding cannot be negative.")


def _default_output(source: Path, requested_slides: list[int] | None, mode: Mode) -> Path:
    label = "all-slides" if requested_slides is None else compact_slide_label(requested_slides)
    return source.with_name(f"{source.stem}_{label}_{mode}_cropped.pdf")


def export_presentation(options: ExportOptions) -> ExportResult:
    _validate_options(options)
    requested_slides = parse_slide_spec(options.slides)
    output = (
        options.output or _default_output(options.source, requested_slides, options.mode)
    ).resolve()
    if output.suffix.lower() != ".pdf":
        raise Pptx2PdfCropError("Output filename must end with .pdf.")
    if output.exists() and not options.force:
        raise Pptx2PdfCropError(f"Output already exists: {output}. Use --force to replace it.")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".pptx2pdfcrop-", dir=output.parent) as temp_name:
        temp_dir = Path(temp_name)
        candidate = temp_dir / "candidate.pdf"

        if options.mode == "compatible":
            raw_tiffs, info, resolved_slides = export_slides_to_tiff(
                options.source,
                temp_dir,
                slides=requested_slides,
                dpi=options.dpi,
            )
            encoded_pages = crop_and_encode_images(
                raw_tiffs,
                resolved_slides,
                temp_dir,
                dpi=options.dpi,
                white_threshold=options.white_threshold,
                padding_points=options.padding_points,
                compression=options.compression,
                jpeg_quality=options.jpeg_quality,
            )
            page_sizes = images_to_pdf(
                encoded_pages,
                candidate,
                title=f"{options.source.stem} - cropped slides",
            )
            result_dpi: int | None = options.dpi
            result_compression: str | None = options.compression
        else:
            native_pdf = temp_dir / "powerpoint-native.pdf"
            working_copy = temp_dir / "working-copy.pptx"
            info, resolved_slides = export_slides_to_vector_pdf(
                options.source,
                native_pdf,
                working_copy,
                slides=requested_slides,
            )
            page_sizes = crop_vector_pdf(
                native_pdf,
                candidate,
                crop_dpi=options.crop_dpi,
                white_threshold=options.white_threshold,
                padding_points=options.padding_points,
            )
            result_dpi = None
            result_compression = None

        if not candidate.is_file() or candidate.stat().st_size == 0:
            raise Pptx2PdfCropError("The export pipeline did not produce a valid PDF.")
        os.replace(candidate, output)

    return ExportResult(
        source=str(options.source.resolve()),
        output=str(output),
        mode=options.mode,
        slides=resolved_slides,
        page_sizes_points=page_sizes,
        bytes=output.stat().st_size,
        dpi=result_dpi,
        compression=result_compression,
        powerpoint_version=info.powerpoint_version,
    )
