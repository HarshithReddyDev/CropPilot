"""Uncertainty engine: first-class uncertain outcomes, never forced.

Every branch returns (status, reason_code, next_action, review_required)
so callers can distinguish "no model exists" from "a model failed".
"""

from __future__ import annotations

from services.disease import errors
from services.disease.fusion import FusionResult
from services.disease.schemas import ImageQuality

RETAKE = (
    "Please take a closer photo of one affected leaf in good daylight, "
    "hold the camera steady, and fill the frame with the affected area."
)

CLOSE_MARGIN = 0.08
LOW_SCORE = 0.50


def decide(
    fused: FusionResult,
    quality_status: str,
    crop_supported: bool,
    vlm_available: bool = False,
) -> tuple[str, str | None, str, bool]:
    """Return (status, reason_code, next_action, review_required)."""
    if quality_status == "rejected":
        return "insufficient_image", errors.POOR_IMAGE_QUALITY, RETAKE, True
    if not crop_supported:
        return (
            "unsupported_crop",
            errors.NO_VERIFIED_MODEL_FOR_CROP,
            "CropPilot does not yet have a verified specialist for this crop. "
            "You can try another photo, or ask the assistant for general guidance.",
            True,
        )
    if not fused.findings:
        return "uncertain", errors.LOW_CONFIDENCE, "No specialist produced evidence. " + RETAKE, True
    top = fused.findings[0]
    second = fused.findings[1] if len(fused.findings) > 1 else None
    if (top.raw_score or 0) < LOW_SCORE or top.confidence_band in {"low", "unknown"}:
        return "uncertain", errors.LOW_CONFIDENCE, "Evidence is weak. " + RETAKE, True
    if second is not None and abs((top.raw_score or 0) - (second.raw_score or 0)) < CLOSE_MARGIN:
        return (
            "uncertain",
            errors.SPECIALIST_DISAGREEMENT,
            f"Patterns overlap between {top.display_name} and {second.display_name}. " + RETAKE,
            True,
        )
    if top.agreement_count >= 2 and top.confidence_band in {"unverified", "high"}:
        return "diagnosed", None, (
            f"Patterns look consistent with {top.display_name}. "
            "This is a likely match, not a laboratory diagnosis; "
            "consider confirming with a local extension officer."
        ), False
    if quality_status == "poor":
        return "probable", errors.LOW_CONFIDENCE, (
            f"Patterns suggest {top.display_name}, but photo quality is poor. {RETAKE}"
        ), True
    _ = ImageQuality  # keep schema import live for type-checkers
    _ = vlm_available
    return "probable", None, (
        f"Patterns suggest {top.display_name}. This is a possible match, "
        "not a laboratory diagnosis."
    ), True
