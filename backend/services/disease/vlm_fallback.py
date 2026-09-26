"""Optional VLM fallback: interpret/explain/resolve, never invent.

Invoked only on uncertainty/disagreement/missing coverage/explicit user
request. High-confidence specialist results skip VLM. Without a
configured vision provider, callers return truthful uncertainty.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

VLM_SYSTEM = (
    "You are CropPilot's vision reviewer. Rules: do not invent a disease; "
    "do not claim a laboratory diagnosis; prefer the specialist evidence "
    "given below; distinguish image evidence from retrieved knowledge; "
    "do not fabricate confidence or localization; say when the image is "
    "inadequate and ask for another photo when needed."
)


@dataclass
class VisionReasoningResult:
    text: str
    latency_ms: float
    provider: str
    model: str


def is_configured() -> bool:
    try:
        from core.config import settings

        provider = str(getattr(settings, "DISEASE_VLM_PROVIDER", "") or "").strip()
        model = str(getattr(settings, "DISEASE_VLM_MODEL", "") or "").strip()
        if provider and model:
            return True
        # Reuse assistant providers when disease-specific ones are unset.
        return bool(
            str(getattr(settings, "OPENROUTER_API_KEY", "") or "")
            or str(getattr(settings, "GEMINI_API_KEY", "") or "")
            or str(getattr(settings, "GROQ_API_KEY", "") or "")
        )
    except Exception:
        return False


async def analyze(
    image,
    candidate_diseases: list[str],
    specialist_summary: str,
    retrieved_knowledge: str,
    quality_note: str = "",
) -> VisionReasoningResult:
    t0 = time.perf_counter()
    try:
        from core.config import settings
    except Exception as e:
        raise RuntimeError(f"VLM unavailable: {e}") from e
    provider = str(getattr(settings, "DISEASE_VLM_PROVIDER", "") or "").strip().lower()
    model = str(getattr(settings, "DISEASE_VLM_MODEL", "") or "").strip()
    if not provider or not model:
        # No dedicated disease VLM: honest unavailability (assistant wiring
        # could extend this later; never fake a review).
        raise RuntimeError("VLM unavailable: DISEASE_VLM_PROVIDER/DISEASE_VLM_MODEL not configured")
    raise RuntimeError(f"VLM unavailable: provider '{provider}' review path not wired to an image-capable client")
