from pptx2pdfcrop import __version__
from pptx2pdfcrop.cli import build_parser


def test_export_parser_defaults_to_vector_mode() -> None:
    args = build_parser().parse_args(["export", "figure.pptx", "--slides", "2"])

    assert args.mode == "vector"
    assert args.crop_dpi == 576
    assert args.white_threshold == 255


def test_package_version_is_available() -> None:
    assert __version__ == "0.1.0"
