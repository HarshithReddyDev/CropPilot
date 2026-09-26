"""Voice session protocol: WS /ws/voice, 16 kHz PCM16 mono in, audio out.

Client -> server (JSON text frames):
  {"type": "config", "lang": "te", "persist_audio": false}
  {"type": "audio", "data": "<base64 pcm16>", "sample_rate": 16000}
  {"type": "commit"}          end of utterance, transcribe + answer + speak
  {"type": "stop"}            barge-in, cancel in-flight TTS

Server -> client:
  {"type": "ready", "asr": ..., "tts": ..., "persist_audio": false}
  {"type": "interim", "text": ...}
  {"type": "final", "text": ...}
  {"type": "response", "text": ...}
  {"type": "audio", "data": "<base64>"} ... {"type": "audio_end"}
  {"type": "error", "code": ..., "message": ...}

Privacy: audio is never written anywhere unless ASSISTANT_PERSIST_AUDIO
is true AND the client opts in. There is no code path that persists
audio when the flag is false, so a config mistake fails closed.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

import structlog
from prometheus_client import Histogram

from core.config import settings

logger = structlog.get_logger(__name__)

SAMPLE_RATE = 16000
# 60 s of 16 kHz mono PCM16; beyond this the buffer is rejected, not grown.
MAX_AUDIO_BYTES = SAMPLE_RATE * 2 * 60
# Base64 audio frames stay small enough for proxies and the WS layer.
AUDIO_CHUNK_BYTES = 3 * 1024

VOICE_LATENCY = Histogram(
    "croppilot_voice_latency_seconds",
    "End-of-utterance to first TTS audio byte.",
    buckets=(0.25, 0.5, 1.0, 1.2, 2.0, 2.5, 5.0, 10.0),
)


class ASRAdapter(ABC):
    name = "disabled"

    @abstractmethod
    async def transcribe(self, pcm: bytes, lang: str, *, final: bool) -> str:
        """Transcribe raw PCM16 mono audio. Empty string means no speech."""

    def supported_languages(self) -> list[str]:
        """Short codes this engine can actually transcribe. Empty = none."""
        return []

    def readiness(self) -> dict:
        return {"available": False, "ready": False, "languages": [],
                "device": "none", "model": "", "error": "engine not configured"}


class DisabledASR(ASRAdapter):
    name = "disabled"

    async def transcribe(self, pcm: bytes, lang: str, *, final: bool) -> str:
        raise RuntimeError("ASR is not configured (no engine available)")


#: Short codes faster-whisper (Whisper) genuinely supports, verified
#: against faster_whisper.tokenizer._LANGUAGE_CODES in the installed
#: faster-whisper 1.2.1. Codes outside this set are refused rather than
#: hallucinated through auto-detect.
FW_SUPPORTED = frozenset({
    "en", "hi", "te", "ta", "bn", "mr", "gu", "kn", "ml", "pa",
    "as", "ne", "ur", "sa", "sd",
})


class FasterWhisperASR(ASRAdapter):
    """Local faster-whisper ASR, lazy-loaded on first use.

    Model/size/device come from settings (ASSISTANT_ASR_MODEL, tristate
    device auto). Transcription runs in a worker thread; the event loop
    never blocks on inference.
    """

    name = "faster-whisper"
    _model: Any = None
    _model_key: str | None = None

    def supported_languages(self) -> list[str]:
        return sorted(FW_SUPPORTED)

    def readiness(self) -> dict:
        # Download-free: never triggers weight fetching. available =
        # library installed AND weights cached; ready = resident in RAM.
        try:
            import faster_whisper  # noqa: F401  # type: ignore[import-not-found]
        except ImportError as e:
            return {"available": False, "ready": False, "languages": [],
                    "device": "none", "model": "",
                    "error": "faster-whisper is not installed"}
        try:
            from huggingface_hub import try_to_load_from_cache

            cached = try_to_load_from_cache("Systran/faster-whisper-base", "model.bin")
        except Exception:
            cached = None
        loaded = type(self)._model is not None
        if cached is None:
            return {"available": False, "ready": False, "languages": [],
                    "device": "none", "model": self._model_id(),
                    "error": "weights not cached; first transcription downloads them"}
        return {"available": True, "ready": loaded,
                "languages": self.supported_languages() if loaded else [],
                "device": self._device(), "model": self._model_id(),
                "error": ""}

    @staticmethod
    def _model_id() -> str:
        return (settings.ASSISTANT_ASR_MODEL or "base").strip() or "base"

    @staticmethod
    def _device() -> str:
        device = (settings.ASSISTANT_ASR_DEVICE or "auto").strip().lower()
        if device in ("cpu", "cuda"):
            return device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    async def transcribe(self, pcm: bytes, lang: str, *, final: bool) -> str:
        code = (lang or "")[:8].lower()
        if code not in FW_SUPPORTED:
            raise RuntimeError(
                f"ASR language '{lang}' is not supported by faster-whisper; "
                "supported: " + ", ".join(sorted(FW_SUPPORTED))
            )
        model = self._load()
        return await asyncio.to_thread(self._infer, model, pcm, code)

    @staticmethod
    def _infer(model: Any, pcm: bytes, code: str) -> str:
        import numpy as np

        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        if audio.size == 0:
            return ""
        segments, info = model.transcribe(
            audio,
            language=code,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return "".join(s.text for s in segments).strip()

    @classmethod
    def _load(cls) -> Any:
        key = f"{cls._model_id()}@{cls._device()}"
        if cls._model is None or cls._model_key != key:
            try:
                from faster_whisper import WhisperModel  # type: ignore[import-not-found]
            except ImportError as e:
                raise RuntimeError(
                    "faster-whisper is not installed; "
                    "set ASSISTANT_ASR_ENGINE='' to disable voice input"
                ) from e
            compute = "float16" if cls._device() == "cuda" else "int8"
            cls._model = WhisperModel(cls._model_id(), device=cls._device(), compute_type=compute)
            cls._model_key = key
            logger.info("voice_asr_loaded", engine=cls.name, model=key)
        return cls._model


class TTSAdapter(ABC):
    name = "disabled"

    @abstractmethod
    def synthesize(self, text: str, lang: str) -> AsyncIterator[bytes]:
        """Yield raw audio bytes (WAV). One chunk per iteration."""

    def supported_languages(self) -> list[str]:
        return []

    def readiness(self) -> dict:
        return {"available": False, "ready": False, "languages": [],
                "device": "none", "model": "", "error": "engine not configured"}


class DisabledTTS(TTSAdapter):
    name = "disabled"

    async def synthesize(self, text: str, lang: str) -> AsyncIterator[bytes]:  # type: ignore[override]
        raise RuntimeError("TTS is not configured (no engine available)")
        yield b""  # pragma: no cover - keeps this an async generator


#: espeak-ng voice ids verified present in espeak-ng 1.52 data
#: (espeak-ng --voices). Robotic fallback quality, real speech.
ESPEAK_VOICES: dict[str, str] = {
    "en": "en",
    "hi": "hi", "mr": "mr", "bn": "bn", "pa": "pa", "gu": "gu",
    "kn": "kn", "ta": "ta", "te": "te", "ml": "ml", "or": "or",
    "as": "as", "ne": "ne", "ur": "ur",
}


class EspeakTTS(TTSAdapter):
    """espeak-ng subprocess TTS. Explicit robotic fallback: real audio,
    low naturalness. No shell: argv list only, bounded runtime, WAV on
    stdout, nothing written to disk."""

    name = "espeak-ng"

    def supported_languages(self) -> list[str]:
        return sorted(ESPEAK_VOICES)

    def readiness(self) -> dict:
        import shutil

        found = shutil.which("espeak-ng") is not None
        return {"available": found, "ready": found,
                "languages": self.supported_languages() if found else [],
                "device": "cpu", "model": "espeak-ng-data",
                "error": "" if found else "espeak-ng binary not found"}

    async def synthesize(self, text: str, lang: str) -> AsyncIterator[bytes]:
        import shutil
        import subprocess

        code = (lang or "")[:8].lower()
        voice = ESPEAK_VOICES.get(code)
        if voice is None:
            raise RuntimeError(
                f"espeak-ng has no voice for '{lang}'; supported: "
                + ", ".join(sorted(ESPEAK_VOICES))
            )
        if shutil.which("espeak-ng") is None:
            raise RuntimeError("espeak-ng binary not found")
        clip = text.strip()[:2000]
        if not clip:
            return
        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                ["espeak-ng", "-v", voice, "--stdout", clip],
                capture_output=True,
                timeout=int(getattr(settings, "ASSISTANT_TTS_TIMEOUT_S", 30) or 30),
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("espeak-ng timed out") from e
        if proc.returncode != 0 or not proc.stdout:
            raise RuntimeError("espeak-ng synthesis failed")
        yield bytes(proc.stdout)


#: Recommended Indic Parler-TTS voices per language (model card).
#: Official 21 + ks/pa unofficial. Languages absent here are refused,
#: never silently spoken in another language's voice.
PARLER_VOICES: dict[str, str] = {
    "as": "Amit", "bn": "Arjun", "brx": "Bikram", "doi": "Karan",
    "en": "Thoma", "gu": "Yash", "hi": "Rohit", "kn": "Suresh",
    "kok": "Sanjay", "mai": "Aryan", "ml": "Anjali", "mni": "Laishram",
    "mr": "Sanjay", "ne": "Amrita", "or": "Manas", "pa": "Divjot",
    "sa": "Aryan", "sat": "Bikram", "sd": "Amit", "ta": "Jaya",
    "te": "Prakash", "ur": "Amit", "ks": "Karan",
}


class ParlerTTS(TTSAdapter):
    """Indic Parler-TTS (ai4bharat/indic-parler-tts, Apache-2.0), lazy.

    Activates only when the parler_tts library AND the model weights are
    present. Otherwise readiness reports the concrete blocker.
    """

    name = "indic-parler"
    _model: Any = None
    _tok: Any = None
    _desc_tok: Any = None

    def supported_languages(self) -> list[str]:
        return sorted(PARLER_VOICES)

    def readiness(self) -> dict:
        # Download-free: never triggers weight fetching.
        try:
            import parler_tts  # noqa: F401  # type: ignore[import-not-found]
            import transformers  # noqa: F401  # type: ignore[import-not-found]
        except ImportError:
            return {"available": False, "ready": False, "languages": [],
                    "device": "none", "model": "",
                    "error": "parler_tts/transformers not installed"}
        try:
            from huggingface_hub import try_to_load_from_cache

            cached = try_to_load_from_cache(self._model_id(), "config.json")
        except Exception:
            cached = None
        loaded = type(self)._model is not None
        if cached is None:
            return {"available": False, "ready": False, "languages": [],
                    "device": "none", "model": self._model_id(),
                    "error": "weights not cached; first synthesis downloads them"}
        return {"available": True, "ready": loaded,
                "languages": self.supported_languages(),
                "device": self._device(), "model": self._model_id(),
                "error": ""}

    @staticmethod
    def _model_id() -> str:
        return (settings.ASSISTANT_TTS_MODEL or "ai4bharat/indic-parler-tts").strip()

    @staticmethod
    def _device() -> str:
        device = (settings.ASSISTANT_TTS_DEVICE or "auto").strip().lower()
        if device in ("cpu", "cuda"):
            return device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    async def synthesize(self, text: str, lang: str) -> AsyncIterator[bytes]:
        code = (lang or "")[:8].lower()
        voice = PARLER_VOICES.get(code)
        if voice is None:
            raise RuntimeError(f"indic-parler has no voice for '{lang}'")
        clip = text.strip()[:2000]
        if not clip:
            return
        wav = await asyncio.to_thread(self._infer, clip, voice)
        yield wav

    def _infer(self, text: str, voice: str) -> bytes:
        import io

        import torch

        model, tok, desc_tok, device = self._load()
        description = (
            f"{voice}'s voice is clear and natural, at a moderate speed, "
            "with very good recording quality."
        )
        d = desc_tok(description, return_tensors="pt").to(device)
        p = tok(text, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(
                input_ids=d.input_ids, attention_mask=d.attention_mask,
                prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask,
            )
        audio = out.cpu().numpy().squeeze()
        import soundfile as sf  # type: ignore[import-not-found]

        buf = io.BytesIO()
        sf.write(buf, audio, model.config.sampling_rate, format="WAV")
        return buf.getvalue()

    @classmethod
    def _load(cls) -> Any:
        if cls._model is not None:
            return cls._model, cls._tok, cls._desc_tok, cls._device()
        try:
            try:
                # transformers-native modeling (preferred, no extra dep).
                from transformers import ParlerTTSForConditionalGeneration  # type: ignore[import-not-found]
            except Exception:
                # Fallback to the standalone parler_tts library.
                from parler_tts import (  # type: ignore[import-not-found,no-redef]
                    ParlerTTSForConditionalGeneration,
                )
            from transformers import AutoTokenizer  # type: ignore[import-not-found]
        except Exception as e:
            raise RuntimeError(
                "ParlerTTS modeling unavailable (transformers/parler_tts "
                "import failed); espeak-ng remains as fallback"
            ) from e
        model_id = cls._model_id()
        try:
            device = cls._device()
            model = ParlerTTSForConditionalGeneration.from_pretrained(model_id).to(device)
            tok = AutoTokenizer.from_pretrained(model_id)
            desc_tok = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
        except Exception as e:
            raise RuntimeError(
                f"indic-parler model '{model_id}' unavailable offline "
                "(gated download or network required)"
            ) from e
        cls._model, cls._tok, cls._desc_tok = model, tok, desc_tok
        logger.info("voice_tts_loaded", engine=cls.name, model=model_id)
        return cls._model, cls._tok, cls._desc_tok, device


def load_asr() -> ASRAdapter:
    engine = (settings.ASSISTANT_ASR_ENGINE or "").strip().lower()
    if engine in ("", "disabled", "none"):
        return DisabledASR()
    if engine == "faster-whisper":
        try:
            import faster_whisper  # noqa: F401  # type: ignore[import-not-found]
        except ImportError as e:
            logger.warning("voice_asr_unavailable", error=str(e))
            return DisabledASR()
        # No eager _load here: weights download on first real
        # transcription, never on capabilities/health probes.
        return FasterWhisperASR()
    logger.warning("voice_asr_unknown_engine", engine=engine)
    return DisabledASR()


def load_tts() -> TTSAdapter:
    engine = (settings.ASSISTANT_TTS_ENGINE or "auto").strip().lower()
    if engine in ("disabled", "none", ""):
        return DisabledTTS()
    if engine in ("auto", "indic-parler", "parler"):
        adapter: TTSAdapter = ParlerTTS()
        if adapter.readiness()["ready"]:
            return adapter
        fallback = (getattr(settings, "ASSISTANT_TTS_FALLBACK", "") or "").strip().lower()
        if fallback in ("espeak-ng", "espeak"):
            esp = EspeakTTS()
            if esp.readiness()["ready"]:
                logger.info("voice_tts_fallback", engine=esp.name)
                return esp
        logger.warning("voice_tts_unavailable", engine=engine)
        return DisabledTTS()
    if engine in ("espeak-ng", "espeak"):
        esp = EspeakTTS()
        if esp.readiness()["ready"]:
            return esp
        logger.warning("voice_tts_unavailable", engine=engine)
        return DisabledTTS()
    logger.warning("voice_tts_unknown_engine", engine=engine)
    return DisabledTTS()


def voice_readiness() -> dict:
    """Cheap readiness (no inference): installed/initialized/ready states."""
    asr, tts = load_asr(), load_tts()
    a, t = asr.readiness(), tts.readiness()
    return {
        "asr": {"engine": asr.name, **a},
        "tts": {"engine": tts.name, **t},
        "persist_audio": bool(settings.ASSISTANT_PERSIST_AUDIO),
    }


def decode_audio_chunk(data: object, sample_rate: object) -> bytes:
    """Validate and decode one client audio frame. Raises ValueError."""
    if not isinstance(data, str) or len(data) > 4096 * 4 // 3 + 64:
        raise ValueError("audio frame too large (base64 chunks are <= 4096 chars)")
    if sample_rate not in (None, SAMPLE_RATE):
        raise ValueError(f"sample_rate must be {SAMPLE_RATE}")
    try:
        return base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("audio data is not valid base64") from e


def split_audio(raw: bytes) -> list[str]:
    return [
        base64.b64encode(raw[i : i + AUDIO_CHUNK_BYTES]).decode("ascii")
        for i in range(0, len(raw), AUDIO_CHUNK_BYTES)
    ]


def _sanitize_page_context(config: Any) -> dict:
    """Allow-listed page context from a WS config frame. Never raises."""
    from services.assistant.ui_actions import ALLOWED_PAGES

    out: dict = {}
    try:
        if not isinstance(config, dict):
            return out
        route = str(config.get("route") or "")[:64]
        if route.startswith("/") and all(c.isalnum() or c in "-_/" for c in route):
            out["route"] = route
        if config.get("page") in ALLOWED_PAGES:
            out["page"] = config["page"]
        filters = config.get("page_filters")
        if isinstance(filters, dict):
            clean = {
                str(k)[:32]: v for k, v in list(filters.items())[:16]
                if isinstance(v, (str, int, float, bool)) and len(str(v)) <= 128
            }
            if clean:
                out["page_filters"] = clean
    except Exception:
        return {}
    return out


async def run_session(websocket: Any, user: Any, default_lang: str = "te") -> None:
    """Run one WS voice session. Never raises; errors go over the wire."""
    from services.assistant.service import assistant_service
    from services.assistant.ui_actions import validate_ui_actions

    await websocket.accept()
    try:
        config = await asyncio.wait_for(websocket.receive_json(), timeout=15)
    except (asyncio.TimeoutError, Exception):
        await websocket.close(code=4401)
        return
    if not isinstance(config, dict) or config.get("type") != "config":
        await websocket.close(code=4400)
        return
    lang = str(config.get("lang") or config.get("language") or default_lang)[:8]
    # Page-aware voice (§8/32): allow-listed route + scalar filters only.
    # Same rules as the REST _page_context, applied to the WS config dict.
    page_ctx = _sanitize_page_context(config)
    if config.get("persist_audio") and not settings.ASSISTANT_PERSIST_AUDIO:
        await websocket.send_json(
            {"type": "error", "code": "persistence_disabled",
             "message": "Server-side audio retention is disabled."}
        )
    if not settings.ASSISTANT_ENABLE_VOICE:
        await websocket.send_json(
            {"type": "error", "code": "voice_disabled",
             "message": "Voice assistant is disabled on this server."}
        )
        await websocket.close()
        return

    asr, tts = load_asr(), load_tts()
    await websocket.send_json(
        {"type": "ready", "asr": asr.name, "tts": tts.name,
         "persist_audio": bool(settings.ASSISTANT_PERSIST_AUDIO)}
    )

    buffer = bytearray()
    tts_task: asyncio.Task | None = None
    user_id = str(getattr(user, "id", "anonymous"))

    async def speak(text: str, t_commit: float) -> None:
        first = True
        try:
            async for raw in tts.synthesize(text, lang):
                for frame in split_audio(raw):
                    await websocket.send_json({"type": "audio", "data": frame})
                if first:
                    first = False
                    dt = asyncio.get_event_loop().time() - t_commit
                    VOICE_LATENCY.observe(dt)
                    logger.info("voice_latency_seconds", latency=dt, lang=lang)
            await websocket.send_json({"type": "audio_end"})
        except asyncio.CancelledError:
            await websocket.send_json({"type": "audio_end", "interrupted": True})
            raise
        except RuntimeError as e:
            from telemetry.assistant_metrics import TTS_ERRORS

            TTS_ERRORS.labels(engine=tts.name).inc()
            await websocket.send_json(
                {"type": "error", "code": "tts_unavailable", "message": str(e)}
            )

    try:
        while True:
            msg = await websocket.receive_json()
            if not isinstance(msg, dict):
                continue
            kind = msg.get("type")
            if kind == "audio":
                if tts_task and not tts_task.done():
                    continue  # barge-in by voice: ignore speech during TTS
                try:
                    chunk = decode_audio_chunk(msg.get("data"), msg.get("sample_rate"))
                except ValueError as e:
                    await websocket.send_json(
                        {"type": "error", "code": "bad_audio", "message": str(e)}
                    )
                    continue
                if len(buffer) + len(chunk) > MAX_AUDIO_BYTES:
                    await websocket.send_json(
                        {"type": "error", "code": "utterance_too_long",
                         "message": "Utterance exceeds 60 seconds."}
                    )
                    continue
                buffer += chunk
            elif kind == "commit":
                if tts_task and not tts_task.done():
                    continue
                t_commit = asyncio.get_event_loop().time()
                pcm, buffer = bytes(buffer), bytearray()
                if not pcm:
                    continue
                try:
                    text = await asr.transcribe(pcm, lang, final=True)
                except RuntimeError as e:
                    from telemetry.assistant_metrics import STT_ERRORS

                    STT_ERRORS.labels(engine=asr.name).inc()
                    await websocket.send_json(
                        {"type": "error", "code": "asr_unavailable", "message": str(e)}
                    )
                    continue
                if not text:
                    await websocket.send_json(
                        {"type": "error", "code": "no_speech",
                         "message": "No speech recognized."}
                    )
                    continue
                await websocket.send_json({"type": "final", "text": text})
                try:
                    chat_context = {"channel": "voice", "lang": lang, "user_id": user_id}
                    chat_context.update(page_ctx)
                    result = await assistant_service.chat(
                        message=text,
                        context=chat_context,
                        language=lang,
                    )
                except Exception as e:
                    logger.warning("voice_chat_failed", error=str(e))
                    await websocket.send_json(
                        {"type": "error", "code": "assistant_failed",
                         "message": "I couldn't process that. Please try again."}
                    )
                    continue
                answer = str(result.get("text") or "")
                await websocket.send_json(
                    {"type": "response", "text": answer,
                     "citations": result.get("citations", []),
                     "ui_actions": validate_ui_actions(result.get("ui_actions", []))}
                )
                tts_task = asyncio.create_task(speak(answer, t_commit))
            elif kind == "stop":
                if tts_task and not tts_task.done():
                    tts_task.cancel()
            elif kind == "config":
                lang = str(msg.get("lang") or lang)[:8]
    except Exception:
        pass
    finally:
        if tts_task and not tts_task.done():
            tts_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
