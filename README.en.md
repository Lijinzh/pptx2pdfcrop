# pptx2pdfcrop

Windows-only CLI for exporting selected Microsoft PowerPoint slides as tightly cropped,
publication-ready PDFs.

- Website: [lijinzh.github.io/pptx2pdfcrop](https://lijinzh.github.io/pptx2pdfcrop/en/)
- Full Chinese documentation: [README.md](README.md)

The default `vector` pipeline asks PowerPoint for a native PDF, detects visible content at high
resolution, and tightens the PDF page boxes without rasterizing text or drawing objects. The
optional `compatible` pipeline lets PowerPoint flatten complex transparency through a
high-resolution TIFF before creating an image PDF.

## Requirements

- Windows 10 or 11
- Desktop Microsoft PowerPoint
- Python 3.10 or newer

PowerPoint for the web, WPS, macOS, and Linux are not supported.

## Install

```powershell
uv tool install git+https://github.com/Lijinzh/pptx2pdfcrop.git
pptx2pdfcrop doctor
```

## Usage

```powershell
# One slide, default vector mode
pptx2pdfcrop export .\drawing.pptx --slides 9

# Multiple slides and an explicit output path
pptx2pdfcrop export .\drawing.pptx --slides 3,5,9-12 --output .\figures.pdf

# Flatten complex transparency when needed
pptx2pdfcrop export .\drawing.pptx --slides 9 --mode compatible
```

Useful controls include `--white-threshold`, `--padding`, `--crop-dpi`, `--dpi`,
`--jpeg-quality`, `--compression lossless`, `--force`, and `--json`.

## Development

```powershell
uv sync --extra dev
uv run ruff check .
uv run pytest
uv build
```

Unit tests do not launch PowerPoint. End-to-end export verification requires a Windows machine
with desktop PowerPoint installed.

## License

[MIT](LICENSE)
