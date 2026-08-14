from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .errors import Pptx2PdfCropError
from .models import ExportOptions
from .pipeline import export_presentation
from .powerpoint import probe_powerpoint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pptx2pdfcrop",
        description=(
            "Export selected PowerPoint slides to tightly cropped PDFs. "
            "The default vector mode preserves native PDF text and drawing objects."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Export and crop selected slides.")
    export.add_argument("input", type=Path, help="Input .ppt/.pptx/.pptm/.ppsx file.")
    export.add_argument(
        "-s",
        "--slides",
        default="1",
        help="1-based slides, for example 8 or 1,3-5 or all (default: 1).",
    )
    export.add_argument("-o", "--output", type=Path, help="Output PDF path.")
    export.add_argument(
        "--mode",
        choices=("compatible", "vector"),
        default="vector",
        help="vector preserves native PDF objects; compatible flattens transparency.",
    )
    export.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="PowerPoint TIFF export resolution for compatible mode (default: 600).",
    )
    export.add_argument(
        "--compression",
        choices=("jpeg", "lossless"),
        default="jpeg",
        help="Final compatible PDF image compression (default: jpeg).",
    )
    export.add_argument(
        "--jpeg-quality",
        type=int,
        default=92,
        help="JPEG quality, using 4:4:4 chroma (default: 92).",
    )
    export.add_argument(
        "--white-threshold",
        type=int,
        default=255,
        help="Pixels with all channels at or above this value are white (default: 255).",
    )
    export.add_argument(
        "--padding",
        type=float,
        default=0.5,
        metavar="POINTS",
        help="Safety padding around detected content (default: 0.5 pt).",
    )
    export.add_argument(
        "--crop-dpi",
        type=int,
        default=576,
        help="Detection resolution for vector mode (default: 576).",
    )
    export.add_argument("--force", action="store_true", help="Replace an existing output file.")
    export.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable result instead of the human summary.",
    )

    subparsers.add_parser("doctor", help="Check Windows and PowerPoint automation.")
    return parser


def _run_export(args: argparse.Namespace) -> int:
    result = export_presentation(
        ExportOptions(
            source=args.input,
            slides=args.slides,
            output=args.output,
            mode=args.mode,
            dpi=args.dpi,
            compression=args.compression,
            jpeg_quality=args.jpeg_quality,
            crop_dpi=args.crop_dpi,
            white_threshold=args.white_threshold,
            padding_points=args.padding,
            force=args.force,
        )
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False))
    else:
        size_mib = result.bytes / 1024 / 1024
        print(f"Created: {result.output}")
        print(f"Slides: {', '.join(str(number) for number in result.slides)}")
        print(f"Mode: {result.mode}")
        if result.dpi is not None:
            print(f"Raster: {result.dpi} DPI, {result.compression}")
        print(f"Size: {size_mib:.2f} MiB")
    return 0


def _run_doctor() -> int:
    if sys.platform != "win32":
        print("[FAIL] Windows is required.")
        return 1
    available, detail = probe_powerpoint()
    if not available:
        print(f"[FAIL] PowerPoint: {detail}")
        return 1
    print("[OK] Windows")
    print(f"[OK] Microsoft PowerPoint COM {detail}")
    print("[OK] TIFF-compatible and vector export pipelines are available")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return _run_doctor()
        return _run_export(args)
    except (Pptx2PdfCropError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
