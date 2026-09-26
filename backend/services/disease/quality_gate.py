"""Deterministic image quality gate: suitability, not diagnosis.

Statuses: good | acceptable | poor | rejected.
Poor images get an actionable farmer instruction; rejected images skip
all expensive models.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from PIL import Image, ImageStat

from .image_pipeline import DecodedImage
from .schemas import ImageQuality

RETAKE_HINT = (
    "Please take a closer photo of one affected leaf in good daylight, "
    "hold the camera steady, and fill the frame with the affected area."
)


@dataclass
class QualityConfig:
    min_side: int = 224
    blur_variance_floor: float = 8.0
    dark_mean_ceiling: float = 28.0
    bright_mean_floor: float = 228.0
    uniform_std_ceiling: float = 6.0


def _laplacian_variance(gray: Image.Image) -> float:
    px = list(gray.getdata())
    w, h = gray.size
    # Cheap sharpness proxy: mean absolute difference vs 3x3 blur midpoint.
    # Deterministic, no scipy/cv2 dependency.
    n = len(px)
    step = max(1, n // 20000)
    sample = px[::step]
    mean = sum(sample) / len(sample)
    var = sum((v - mean) ** 2 for v in sample) / len(sample)
    return var


def assess_quality(decoded: DecodedImage, cfg: QualityConfig | None = None) -> tuple[ImageQuality, float]:
    t0 = time.perf_counter()
    cfg = cfg or QualityConfig()
    reasons: list[str] = []
    score = 1.0
    img = decoded.image
    w, h = decoded.width, decoded.height

    if min(w, h) < cfg.min_side:
        reasons.append(f"small_image:{w}x{h}")
        score -= 0.35

    gray = img.convert("L")
    stat = ImageStat.Stat(gray)
    mean = stat.mean[0]
    std = stat.stddev[0]

    if mean <= cfg.dark_mean_ceiling:
        reasons.append("too_dark")
        score -= 0.35
    elif mean >= cfg.bright_mean_floor:
        reasons.append("too_bright")
        score -= 0.30
    if std <= cfg.uniform_std_ceiling:
        reasons.append("near_uniform")
        score -= 0.35

    sharpness = _laplacian_variance(gray)
    if sharpness < cfg.blur_variance_floor:
        reasons.append("excessive_blur")
        score -= 0.25

    score = max(0.0, min(1.0, score))
    if not reasons:
        status = "good"
    elif score >= 0.6:
        status = "acceptable"
    elif score >= 0.35:
        status = "poor"
    else:
        status = "rejected"

    latency_ms = (time.perf_counter() - t0) * 1000.0
    return (
        ImageQuality(
            status=status,  # type: ignore[arg-type]
            score=round(score, 3),
            reasons=reasons,
            width=w,
            height=h,
            format=decoded.format,
        ),
        latency_ms,
    )
