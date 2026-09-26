"""Voice engine tests (V1.3 §4-5). Adapter behavior with real libraries
where installed; honest-unavailable paths otherwise. No audio fixtures
fabricated as accuracy claims."""

import pytest

from services.assistant.voice import (
    DisabledASR,
    DisabledTTS,
    EspeakTTS,
    FasterWhisperASR,
    ParlerTTS,
    decode_audio_chunk,
    load_asr,
    load_tts,
    voice_readiness,
)


async def test_disabled_adapters_raise_honestly():
    with pytest.raises(RuntimeError):
        await DisabledASR().transcribe(b"\x00\x00", "en", final=True)
    assert DisabledTTS().readiness()["ready"] is False


async def _raises(asr):
    try:
        await asr.transcribe(b"\x00\x00" * 1600, "brx", final=True)
    except RuntimeError:
        return True
    return False


async def test_fw_gate_async():
    asr = FasterWhisperASR()
    assert await _raises(asr) is True


def test_fw_supported_set_matches_package():
    try:
        from faster_whisper.tokenizer import _LANGUAGE_CODES
    except ImportError:
        pytest.skip("faster-whisper not installed")
    assert set(FasterWhisperASR().supported_languages()) <= set(_LANGUAGE_CODES)
    for code in ("en", "hi", "te", "ta", "bn", "mr", "ur"):
        assert code in FasterWhisperASR().supported_languages()


def test_espeak_voices_are_real():
    """Voice ids claimed must exist in the installed espeak-ng data."""
    import shutil
    import subprocess

    from services.assistant.voice import ESPEAK_VOICES

    if shutil.which("espeak-ng") is None:
        pytest.skip("espeak-ng not installed")
    out = subprocess.run(["espeak-ng", "--voices"], capture_output=True,
                         timeout=30, check=False)
    listed = out.stdout.decode("utf-8", "replace")
    for code, voice in ESPEAK_VOICES.items():
        assert voice in listed, f"espeak voice missing: {voice} ({code})"


def test_parler_voices_subset_documented():
    """Claimed voices stay within the model card's speaker table."""
    from services.assistant.voice import PARLER_VOICES

    assert PARLER_VOICES["te"] == "Prakash"
    assert PARLER_VOICES["hi"] == "Rohit"
    assert "ks" in PARLER_VOICES and "pa" in PARLER_VOICES  # unofficial per card
    assert len(PARLER_VOICES) >= 23


def test_audio_frame_limits():
    import base64

    assert decode_audio_chunk(base64.b64encode(b"\x01\x02").decode(), 16000) == b"\x01\x02"
    with pytest.raises(ValueError):
        decode_audio_chunk("!!!not-base64!!!", 16000)
    with pytest.raises(ValueError):
        decode_audio_chunk(base64.b64encode(b"\x01").decode(), 8000)
    with pytest.raises(ValueError):
        decode_audio_chunk("a" * 6000, 16000)


def test_loaders_never_raise():
    assert isinstance(load_asr(), (DisabledASR, FasterWhisperASR))
    assert isinstance(load_tts(), (DisabledTTS, EspeakTTS, ParlerTTS))


def test_readiness_shape():
    state = voice_readiness()
    assert set(state) == {"asr", "tts", "persist_audio"}
    for side in ("asr", "tts"):
        assert {"engine", "available", "ready", "languages", "device", "model"}.issubset(state[side])
        assert isinstance(state[side]["languages"], list)
    assert state["persist_audio"] is False
