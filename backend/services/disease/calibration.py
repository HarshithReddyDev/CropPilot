"""Score calibration abstraction.

No validated calibration artifact ships, so scores are reported
honestly as raw_model_score with conservative heuristic bands.
Temperature/isotonic calibration can plug in later via
Calibrator artifacts without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass

HIGH_RAW = 0.75
MEDIUM_RAW = 0.50


@dataclass
class CalibrationArtifact:
    version: str
    kind: str  # e.g. "temperature" | "isotonic"
    params: dict


def heuristic_band(raw_score: float | None) -> str:
    if raw_score is None:
        return "unknown"
    if raw_score >= HIGH_RAW:
        return "high"
    if raw_score >= MEDIUM_RAW:
        return "medium"
    return "low"


def calibrate(
    raw_score: float | None,
    artifact: CalibrationArtifact | None = None,
) -> tuple[float | None, str, str]:
    """Return (score, score_type, confidence_band).

    Without an artifact the score_type is "raw_model_score" and the band
    is the conservative heuristic. With an artifact the caller must have
    validated it on held-out field data; then score_type is "calibrated".
    """
    if artifact is None or raw_score is None:
        band = heuristic_band(raw_score) if raw_score is not None else "unknown"
        # Honest label: uncalibrated softmax is not a probability.
        return raw_score, "raw_model_score", "unverified" if raw_score is not None and raw_score >= HIGH_RAW else band
    # Placeholder path for a real validated artifact (temperature example).
    t = float(artifact.params.get("temperature", 1.0) or 1.0)
    import math

    logit = math.log(max(raw_score, 1e-6) / max(1 - raw_score, 1e-6))
    cal = 1.0 / (1.0 + math.exp(-logit / max(t, 1e-3)))
    return cal, "calibrated", heuristic_band(cal)
