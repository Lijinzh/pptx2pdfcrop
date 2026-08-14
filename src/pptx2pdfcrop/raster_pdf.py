from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import img2pdf
from PIL import Image
from pypdf import PdfReader

from .geometry import CropBox, crop_raster_image


@dataclass(frozen=True)
class RasterPageResult:
    slide_number: int
    source_pixels: tuple[int, int]
    cropped_pixels: tuple[int, int]
    crop_box: CropBox
    encoded_path: Path


def crop_and_encode_images(
    raw_tiffs: list[Path],
    slide_numbers: list[int],
    output_dir: Path,
    *,
    dpi: int,
    white_threshold: int,
    padding_points: float,
    compression: str,
    jpeg_quality: int,
) -> list[RasterPageResult]:
    if len(raw_tiffs) != len(slide_numbers):
        raise ValueError("raw_tiffs and slide_numbers must have equal length.")

    padding_pixels = round(padding_points / 72.0 * dpi)
    results: list[RasterPageResult] = []
    for sequence, (raw_tiff, slide_number) in enumerate(
        zip(raw_tiffs, slide_numbers, strict=True),
        start=1,
    ):
        with Image.open(raw_tiff) as opened:
            source = opened.convert("RGB")
            cropped, crop_box = crop_raster_image(
                source,
                white_threshold=white_threshold,
                padding_pixels=padding_pixels,
            )
            source_size = source.size

        if compression == "jpeg":
            encoded = output_dir / f"cropped-{sequence:04d}-slide-{slide_number}.jpg"
            cropped.save(
                encoded,
                format="JPEG",
                quality=jpeg_quality,
                subsampling=0,
                optimize=True,
                progressive=False,
                dpi=(dpi, dpi),
            )
        elif compression == "lossless":
            encoded = output_dir / f"cropped-{sequence:04d}-slide-{slide_number}.tif"
            cropped.save(
                encoded,
                format="TIFF",
                compression="tiff_lzw",
                dpi=(dpi, dpi),
            )
        else:
            raise ValueError(f"Unsupported compression: {compression}")

        results.append(
            RasterPageResult(
                slide_number=slide_number,
                source_pixels=source_size,
                cropped_pixels=cropped.size,
                crop_box=crop_box,
                encoded_path=encoded,
            )
        )
    return results


def images_to_pdf(
    pages: list[RasterPageResult],
    output_pdf: Path,
    *,
    title: str,
) -> list[tuple[float, float]]:
    """Embed pre-encoded images without another quality-reducing recompression pass."""

    pdf_bytes = img2pdf.convert(
        *[str(page.encoded_path) for page in pages],
        title=title,
        producer="pptx2pdfcrop",
    )
    output_pdf.write_bytes(pdf_bytes)

    reader = PdfReader(str(output_pdf))
    return [(float(page.mediabox.width), float(page.mediabox.height)) for page in reader.pages]
