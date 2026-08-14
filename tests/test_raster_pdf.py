from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from pptx2pdfcrop.raster_pdf import crop_and_encode_images, images_to_pdf


def test_jpeg_pdf_is_cropped_and_uses_image_page_size(tmp_path: Path) -> None:
    raw = tmp_path / "raw.tif"
    output = tmp_path / "output.pdf"
    image = Image.new("RGB", (600, 400), "white")
    image.paste((30, 100, 200), (100, 50, 500, 350))
    image.save(raw, format="TIFF", compression="tiff_lzw", dpi=(300, 300))

    pages = crop_and_encode_images(
        [raw],
        [8],
        tmp_path,
        dpi=300,
        white_threshold=255,
        padding_points=0,
        compression="jpeg",
        jpeg_quality=94,
    )
    sizes = images_to_pdf(pages, output, title="test")

    assert pages[0].cropped_pixels == (400, 300)
    assert output.is_file()
    assert len(PdfReader(str(output)).pages) == 1
    assert abs(sizes[0][0] - 96.0) < 0.2
    assert abs(sizes[0][1] - 72.0) < 0.2
