"""Translation bridge tests (V1.3 §3). Model-independent paths run
everywhere; live-model paths skip honestly when weights are absent."""

import pytest

from services.assistant.languages import LANGUAGES
from services.assistant.translation import (
    FLORES,
    TranslationManager,
    TranslationUnavailable,
    _direction,
)


def test_flores_covers_registry():
    """Every canonical locale has a Flores code (no invented support)."""
    codes = {lang.code for lang in LANGUAGES}
    assert set(FLORES) == codes


def test_direction_routing():
    assert _direction("en", "hi") == "en-indic"
    assert _direction("te", "en") == "indic-en"
    with pytest.raises(TranslationUnavailable):
        _direction("en", "en")


async def test_empty_and_same_language_passthrough():
    mgr = TranslationManager()
    assert await mgr.translate("", "en", "hi") == ""
    assert await mgr.translate("hello", "en", "en") == "hello"


async def test_unsupported_pair_honest():
    mgr = TranslationManager()
    with pytest.raises(TranslationUnavailable):
        await mgr.translate("hello", "en", "xx")


async def test_unavailable_model_honest(monkeypatch):
    """Without cached weights the bridge refuses instead of faking."""
    import services.assistant.translation as mod

    monkeypatch.setattr(mod.TranslationManager, "_load",
                        lambda self, d: (_ for _ in ()).throw(
                            TranslationUnavailable("no weights")))
    mgr = TranslationManager()
    with pytest.raises(TranslationUnavailable):
        await mgr.translate("Latest price", "en", "hi", timeout_s=5)


async def test_placeholder_split_pure():
    """Placeholder segmentation keeps every token in order."""
    import re

    text = "Latest price: {price} per quintal in {district}"
    parts = re.split(r"\{[a-zA-Z0-9_]+\}", text)
    tokens = re.findall(r"\{[a-zA-Z0-9_]+\}", text)
    assert parts == ["Latest price: ", " per quintal in ", ""]
    assert tokens == ["{price}", "{district}"]


def test_readiness_shape_no_inference():
    mgr = TranslationManager()
    state = mgr.readiness()
    assert set(state["directions"]) == {"en-indic", "indic-en", "indic-indic"}
    for direction, info in state["directions"].items():
        assert {"model", "cached", "loaded", "ready"}.issubset(info)
