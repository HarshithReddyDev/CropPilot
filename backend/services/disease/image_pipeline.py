"""Image pipeline: decode (PIL only, no cv2), EXIF orientation, resize,
deterministic region crops. Never logs image bytes."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps

from . import errors
from .errors import DiseaseError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_PIXELS_DEFAULT = 25_000_000


@dataclass
class DecodedImage:
    image: Image.Image
    format: str
    width: int
    height: int


def decode_image(data: bytes, max_pixels: int = MAX_PIXELS_DEFAULT) -> DecodedImage:
    if not data or len(data) < 64:
        raise DiseaseError(errors.IMAGE_INVALID, "Empty or truncated image payload.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        raise DiseaseError(errors.IMAGE_INVALID, "File could not be decoded as an image.")
    fmt = (img.format or "unknown").upper()
    if fmt not in ALLOWED_FORMATS:
        # Re-encode check: some valid images lack format tags; verify by conversion
        try:
            img.convert("RGB")
        except Exception:
            raise DiseaseError(errors.IMAGE_INVALID, f"Unsupported image format: {fmt}.")
        fmt = "JPEG" if fmt == "UNKNOWN" else fmt
    w, h = img.size
    if w * h > max_pixels:
        raise DiseaseError(errors.IMAGE_TOO_LARGE, "Image exceeds the pixel limit.")
    if w < 32 or h < 32:
        raise DiseaseError(errors.IMAGE_INVALID, "Image is too small to analyze.")
    img = ImageOps.exif_transpose(img)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return DecodedImage(image=img, format=fmt, width=w, height=h)


def resize_for_inference(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    if img.size == size:
        return img
    return img.resize(size, Image.BILINEAR)


@dataclass
class ImageRegion:
    kind: str
    box: tuple[float, float, float, float]  # normalized x1,y1,x2,y2
    source: str
    pixels: Image.Image


def make_regions(
    img: Image.Image, max_crops: int = 3, crop_ratio: float = 0.75
) -> list[ImageRegion]:
    """Full image + deterministic center/corner crops. Never lesion claims."""
    w, h = img.size
    regions = [ImageRegion(kind="full", box=(0.0, 0.0, 1.0, 1.0), source="deterministic", pixels=img)]
    if max_crops <= 0:
        return regions
    cw, ch = int(w * crop_ratio), int(h * crop_ratio)
    boxes = [
        ("center_crop", ((w - cw) // 2, (h - ch) // 2)),
        ("crop", (0, 0)),
        ("crop", (w - cw, h - ch)),
    ]
    for kind, (x, y) in boxes[:max_crops]:
        crop = img.crop((x, y, x + cw, y + ch))
        regions.append(
            ImageRegion(
                kind=kind,
                box=(x / w, y / h, (x + cw) / w, (y + ch) / h),
                source="deterministic",
                pixels=crop,
            )
        )
    return regions
