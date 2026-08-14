class Pptx2PdfCropError(RuntimeError):
    """Base error shown to CLI users without a Python traceback."""


class BackendUnavailableError(Pptx2PdfCropError):
    """Raised when neither PowerPoint nor LibreOffice is available."""


class SlideSelectionError(Pptx2PdfCropError):
    """Raised when a requested slide number is invalid."""


class CropError(Pptx2PdfCropError):
    """Raised when visible content cannot be detected safely."""
