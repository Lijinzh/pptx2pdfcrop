from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

Mode = Literal["compatible", "vector"]
Compression = Literal["jpeg", "lossless"]


@dataclass(frozen=True)
class ExportOptions:
    """User-facing options for one PowerPoint export operation."""

    source: Path
    slides: str = "1"
    output: Path | None = None
    mode: Mode = "vector"
    dpi: int = 600
    compression: Compression = "jpeg"
    jpeg_quality: int = 92
    crop_dpi: int = 576
    white_threshold: int = 255
    padding_points: float = 0.5
    force: bool = False


@dataclass(frozen=True)
class ExportResult:
    """Serializable summary returned after a successful export."""

    source: str
    output: str
    mode: Mode
    slides: list[int]
    page_sizes_points: list[tuple[float, float]]
    bytes: int
    dpi: int | None
    compression: Compression | None
    powerpoint_version: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
