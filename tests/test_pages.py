import pytest

from pptx2pdfcrop.errors import SlideSelectionError
from pptx2pdfcrop.models import ExportOptions
from pptx2pdfcrop.pages import parse_slide_spec, resolve_slides


def test_parse_slide_spec() -> None:
    assert parse_slide_spec("8") == [8]
    assert parse_slide_spec("1,3-5,3") == [1, 3, 4, 5]
    assert parse_slide_spec("all") is None


@pytest.mark.parametrize("spec", ["", "0", "3-1", "1,,2", "a", "1-2-3"])
def test_reject_invalid_slide_spec(spec: str) -> None:
    with pytest.raises(SlideSelectionError):
        parse_slide_spec(spec)


def test_resolve_slides() -> None:
    assert resolve_slides(None, 3) == [1, 2, 3]
    assert resolve_slides([2], 3) == [2]
    with pytest.raises(SlideSelectionError):
        resolve_slides([4], 3)


def test_default_export_mode_is_vector(tmp_path) -> None:
    assert ExportOptions(source=tmp_path / "figure.pptx").mode == "vector"
