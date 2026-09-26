"""IndicTrans2 runtime translation bridge (V1.3 §3).

Policy: direct multilingual reasoning first (the LLM answers in the
user's language without any bridge). The bridge runs ONLY when a caller
explicitly needs it: weak-language fallback, cross-language retrieval,
or voice-pipeline text. Never translate citations themselves.

Models (AI4Bharat, MIT checkpoints): dist-200M per direction, lazy,
CPU/GPU auto. No network after weights are cached. No audio, no secrets.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import structlog

from core.config import settings

logger = structlog.get_logger(__name__)

#: Short code -> Flores-200 code used by IndicTrans2.
FLORES: dict[str, str] = {
    "en": "eng_Latn", "as": "asm_Beng", "bn": "ben_Beng",
    "brx": "brx_Deva", "doi": "doi_Deva", "gu": "guj_Gujr",
    "hi": "hin_Deva", "kn": "kan_Knda", "ks": "kas_Arab",
    "kok": "gom_Deva", "mai": "mai_Deva", "ml": "mal_Mlym",
    "mni": "mni_Beng", "mr": "mar_Deva", "ne": "nep_Deva",
    "or": "ory_Orya", "pa": "pan_Guru", "sa": "san_Deva",
    "sat": "sat_Olck", "sd": "snd_Arab", "ta": "tam_Taml",
    "te": "tel_Telu", "ur": "urd_Arab",
}

DIRECTIONS = ("en-indic", "indic-en", "indic-indic")

_PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z0-9_]+\}")


class TranslationUnavailable(RuntimeError):
    """Bridge cannot serve this pair right now (reason in message)."""


def _direction(src: str, tgt: str) -> str:
    if src == "en" and tgt != "en":
        return "en-indic"
    if tgt == "en" and src != "en":
        return "indic-en"
    if src != "en" and tgt != "en":
        return "indic-indic"
    raise TranslationUnavailable("noop translation (same language)")


def _model_id(direction: str) -> str:
    override = (getattr(settings, "ASSISTANT_MT_MODEL", "") or "").strip()
    if override and direction == "en-indic":
        return override
    base = {
        "en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
        "indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
        "indic-indic": "ai4bharat/indictrans2-indic-indic-dist-200M",
    }[direction]
    return base


class TranslationManager:
    """Lazy per-direction IndicTrans2. One instance process-wide."""

    def __init__(self) -> None:
        self._loaded: dict[str, Any] = {}
        self._sem = asyncio.Semaphore(
            max(1, int(getattr(settings, "ASSISTANT_MT_CONCURRENCY", 1) or 1))
        )

    @staticmethod
    def _device() -> str:
        if (getattr(settings, "ASSISTANT_MT_DEVICE", "auto") or "auto") == "cpu":
            return "cpu"
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def readiness(self) -> dict:
        """Per-direction load state. Loads nothing (checks cache only)."""
        from huggingface_hub import try_to_load_from_cache  # type: ignore[import-not-found]

        out: dict[str, Any] = {"engine": "indictrans2", "directions": {}}
        for direction in DIRECTIONS:
            model_id = _model_id(direction)
            try:
                cached = try_to_load_from_cache(model_id, "config.json")
                loaded = direction in self._loaded
                out["directions"][direction] = {
                    "model": model_id,
                    "cached": cached is not None,
                    "loaded": loaded,
                    "ready": cached is not None,
                    "error": "" if cached is not None else "model weights not cached",
                }
            except Exception as e:  # huggingface_hub missing etc.
                out["directions"][direction] = {
                    "model": model_id, "cached": False, "loaded": False,
                    "ready": False, "error": str(e)[:160],
                }
        out["ready"] = any(d["ready"] for d in out["directions"].values())
        return out

    def _load(self, direction: str) -> Any:
        if direction in self._loaded:
            return self._loaded[direction]
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            from IndicTransToolkit.processor import IndicProcessor  # type: ignore[import-not-found]
        except ImportError as e:
            raise TranslationUnavailable(
                f"translation libraries missing ({e}); install transformers + IndicTransToolkit"
            ) from e
        model_id = _model_id(direction)
        device = self._device()
        try:
            tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_id, trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            ).to(device)
            ip = IndicProcessor(inference=True)
        except Exception as e:
            raise TranslationUnavailable(
                f"translation model '{model_id}' unavailable offline ({e})"
            ) from e
        bundle = (model, tok, ip, device)
        self._loaded[direction] = bundle
        logger.info("translation_loaded", direction=direction, model=model_id)
        return bundle

    async def translate(self, text: str, src: str, tgt: str,
                        timeout_s: float | None = None) -> str:
        """Translate, preserving {placeholders}. Raises TranslationUnavailable."""
        src = (src or "")[:8].lower()
        tgt = (tgt or "")[:8].lower()
        if not (text or "").strip():
            return ""
        if src == tgt:
            return text
        if src not in FLORES or tgt not in FLORES:
            raise TranslationUnavailable(f"unsupported pair {src}->{tgt}")
        if src != "en" and tgt != "en":
            # Pivot through English (documented indic-indic alternative).
            mid = await self.translate(text, src, "en", timeout_s=timeout_s)
            return await self.translate(mid, "en", tgt, timeout_s=timeout_s)
        direction = _direction(src, tgt)
        timeout = timeout_s or float(getattr(settings, "ASSISTANT_MT_TIMEOUT_S", 60) or 60)
        async with self._sem:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self._blocking, direction, text, src, tgt),
                    timeout=timeout,
                )
            except asyncio.TimeoutError as e:
                raise TranslationUnavailable("translation timed out") from e

    def _blocking(self, direction: str, text: str, src: str, tgt: str) -> str:
        model, tok, ip, device = self._load(direction)
        import torch

        src_f, tgt_f = FLORES[src], FLORES[tgt]
        # Placeholder-safe: translate segments around {tokens} separately.
        parts = _PLACEHOLDER_RE.split(text)
        tokens = _PLACEHOLDER_RE.findall(text)
        out_parts: list[str] = []
        for i, part in enumerate(parts):
            if part.strip():
                out_parts.append(self._one(model, tok, ip, device, part, src_f, tgt_f, torch))
            else:
                out_parts.append(part)
            if i < len(tokens):
                out_parts.append(tokens[i])
        return "".join(out_parts)

    @staticmethod
    def _one(model: Any, tok: Any, ip: Any, device: str,
             part: str, src_f: str, tgt_f: str, torch: Any) -> str:
        chunks: list[str] = []
        buf = part
        while len(buf) > 800:
            cut = max(buf.rfind(". ", 0, 800), buf.rfind("\n", 0, 800))
            cut = cut + 1 if cut > 0 else 800
            chunks.append(buf[:cut])
            buf = buf[cut:]
        chunks.append(buf)
        rendered: list[str] = []
        for chunk in chunks:
            batch = ip.preprocess_batch([chunk], src_lang=src_f, tgt_lang=tgt_f)
            inputs = tok(batch, truncation=True, padding="longest",
                         return_tensors="pt", return_attention_mask=True).to(device)
            with torch.no_grad():
                gen = model.generate(**inputs, use_cache=True, min_length=0,
                                     max_length=256, num_beams=5, num_return_sequences=1)
            decoded = tok.batch_decode(gen, skip_special_tokens=True,
                                       clean_up_tokenization_spaces=True)
            rendered.extend(ip.postprocess_batch(decoded, lang=tgt_f))
        return "".join(rendered)


translation_manager = TranslationManager()
