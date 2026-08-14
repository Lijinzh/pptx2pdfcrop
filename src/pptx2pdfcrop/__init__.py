"""PowerPoint slide export and tight-crop utilities."""

from importlib.metadata import PackageNotFoundError, version

from .models import ExportOptions, ExportResult
from .pipeline import export_presentation

__all__ = ["ExportOptions", "ExportResult", "export_presentation"]

try:
    __version__ = version("pptx2pdfcrop")
except PackageNotFoundError:
    __version__ = "0.1.0"
