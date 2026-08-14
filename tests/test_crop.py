from pathlib import Path

import img2pdf
import pytest
from PIL import Image
from pypdf import PdfReader

from pptx2pdfcrop.errors import CropError
from pptx2pdfcrop.geometry import crop_raster_image, detect_visible_bbox
from pptx2pdfcrop.vector_pdf import crop_vector_pdf


def test_detect_and_crop_white_border() -> None:
    image = Image.new("RGB", (100, 80), "white")
    image.paste((10, 20, 30), (20, 10, 90, 70))

    box = detect_visible_bbox(image, 255)
    assert box.as_tuple() == (20, 10, 90, 70)

    cropped, expanded = crop_raster_image(
        image,
        white_threshold=255,
        padding_pixels=2,
    )
    assert expanded.as_tuple() == (18, 8, 92, 72)
    assert cropped.size == (74, 64)


def test_white_threshold_controls_near_white_pixels() -> None:
    image = Image.new("RGB", (20, 20), "white")
    image.putpixel((10, 10), (252, 252, 252))

    assert detect_visible_bbox(image, 255).as_tuple() == (10, 10, 11, 11)
    with pytest.raises(CropError):
        detect_visible_bbox(image, 250)


def test_crop_vector_pdf_changes_page_box_without_flattening(tmp_path: Path) -> None:
    image_path = tmp_path / "bordered.jpg"
    source_pdf = tmp_path / "source.pdf"
    output_pdf = tmp_path / "cropped.pdf"

    image = Image.new("RGB", (400, 300), "white")
    image.paste((0, 0, 0), (100, 75, 300, 225))
    image.save(image_path, quality=95, dpi=(100, 100))
    source_pdf.write_bytes(img2pdf.convert(str(image_path)))

    sizes = crop_vector_pdf(
        source_pdf,
        output_pdf,
        crop_dpi=288,
        white_threshold=250,
        padding_points=0,
    )
    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 1
    assert sizes[0][0] < float(PdfReader(str(source_pdf)).pages[0].mediabox.width)
    assert sizes[0][1] < float(PdfReader(str(source_pdf)).pages[0].mediabox.height)
