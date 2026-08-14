from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject

from .errors import CropError
from .geometry import detect_visible_bbox, expand_bbox


def crop_vector_pdf(
    source_pdf: Path,
    output_pdf: Path,
    *,
    page_numbers: list[int] | None = None,
    crop_dpi: int = 576,
    white_threshold: int = 255,
    padding_points: float = 0.5,
) -> list[tuple[float, float]]:
    """Tighten PDF page boxes while preserving original PDF content streams."""

    if crop_dpi < 72:
        raise ValueError("crop_dpi must be at least 72.")
    if padding_points < 0:
        raise ValueError("padding_points cannot be negative.")

    reader = PdfReader(str(source_pdf))
    selected = page_numbers or list(range(1, len(reader.pages) + 1))
    invalid = [number for number in selected if number < 1 or number > len(reader.pages)]
    if invalid:
        raise CropError(f"PDF page selection is out of range: {invalid}")

    rendered_document = pdfium.PdfDocument(str(source_pdf))
    writer = PdfWriter()
    page_sizes: list[tuple[float, float]] = []
    scale = crop_dpi / 72.0

    try:
        for page_number in selected:
            source_page = reader.pages[page_number - 1]
            rotation = int(source_page.get("/Rotate", 0) or 0) % 360
            if rotation != 0:
                raise CropError(
                    f"Page {page_number} has a {rotation}-degree rotation, which is not "
                    "currently supported for vector cropping."
                )

            rendered = (
                rendered_document[page_number - 1].render(scale=scale).to_pil().convert("RGB")
            )
            pixel_box = expand_bbox(
                detect_visible_bbox(rendered, white_threshold),
                round(padding_points * scale),
                rendered.size,
            )

            page_width = float(source_page.mediabox.width)
            page_height = float(source_page.mediabox.height)
            x_scale = rendered.width / page_width
            y_scale = rendered.height / page_height

            left = pixel_box.left / x_scale
            right = pixel_box.right / x_scale
            top = page_height - pixel_box.top / y_scale
            bottom = page_height - pixel_box.bottom / y_scale
            cropped_width = right - left
            cropped_height = top - bottom

            writer.add_page(source_page)
            target_page = writer.pages[-1]
            target_page.add_transformation(
                Transformation().translate(tx=-left, ty=-bottom),
                expand=False,
            )
            new_box = RectangleObject([0, 0, cropped_width, cropped_height])
            target_page.mediabox = new_box
            target_page.cropbox = RectangleObject(new_box)
            target_page.trimbox = RectangleObject(new_box)
            target_page.bleedbox = RectangleObject(new_box)
            target_page.artbox = RectangleObject(new_box)
            page_sizes.append((cropped_width, cropped_height))
    finally:
        rendered_document.close()

    if reader.metadata:
        metadata = {key: str(value) for key, value in reader.metadata.items() if value is not None}
        writer.add_metadata(metadata)
    with output_pdf.open("wb") as stream:
        writer.write(stream)
    return page_sizes
