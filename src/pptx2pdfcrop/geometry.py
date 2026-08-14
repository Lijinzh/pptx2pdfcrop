from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageChops

from .errors import CropError


@dataclass(frozen=True)
class CropBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.right, self.bottom


def detect_visible_bbox(image: Image.Image, white_threshold: int = 255) -> CropBox:
    """Return the bounds of pixels that are not sufficiently white."""

    if not 1 <= white_threshold <= 255:
        raise ValueError("white_threshold must be between 1 and 255.")

    red, green, blue = image.convert("RGB").split()
    darkest_channel = ImageChops.darker(ImageChops.darker(red, green), blue)
    mask = darkest_channel.point(lambda value: 255 if value < white_threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        raise CropError("The selected page appears to be completely white.")
    return CropBox(*bbox)


def expand_bbox(box: CropBox, padding_pixels: int, image_size: tuple[int, int]) -> CropBox:
    width, height = image_size
    return CropBox(
        left=max(0, box.left - padding_pixels),
        top=max(0, box.top - padding_pixels),
        right=min(width, box.right + padding_pixels),
        bottom=min(height, box.bottom + padding_pixels),
    )


def crop_raster_image(
    image: Image.Image,
    *,
    white_threshold: int,
    padding_pixels: int,
) -> tuple[Image.Image, CropBox]:
    box = expand_bbox(
        detect_visible_bbox(image, white_threshold),
        padding_pixels,
        image.size,
    )
    return image.crop(box.as_tuple()).convert("RGB"), box
