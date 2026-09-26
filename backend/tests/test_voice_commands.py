"""Voice/text command golden set (V1.3 §54). 10 en + 10 te/te-translit +
10 hi/hi-translit. Tests the deterministic matcher only — NOT speech
accuracy (no fabricated audio). Each case: input, language, expected
intent, expected tools (always none: commands bypass tools), expected
UI action, expected language effect."""

from services.assistant.commands import command_actions


CASES = [
    # English (10)
    ("Open markets page", "en", "navigate", [], "navigation.open_page:markets", None),
    ("Go to weather", "en", "navigate", [], "navigation.open_page:weather", None),
    ("Open disease detection", "en", "navigate", [], "navigation.open_page:disease-detection", None),
    ("Show tomato prices in Nalgonda.", "en", "market", [], None, None),
    ("What schemes are available for farmers?", "en", "scheme", [], None, None),
    ("Switch to Telugu", "en", "language", [], "assistant.set_language:te", "te"),
    ("Change language to Hindi", "en", "language", [], "assistant.set_language:hi", "hi"),
    ("Open analytics", "en", "navigate", [], "navigation.open_page:analytics", None),
    ("Open maps", "en", "navigate", [], "navigation.open_page:maps", None),
    ("naviguate to schemes", "en", "other", [], None, None),  # typo: no match
    # Telugu + transliteration (10)
    ("market open cheyyi", "te", "navigate", [], "navigation.open_page:markets", None),
    ("నల్గొండలో టమాటా ధర చూపించు", "te", "market", [], None, None),
    ("తెలుగుకు మార్చు", "te", "language", [], "assistant.set_language:te", "te"),
    ("mandi kholo", "te", "navigate", [], "navigation.open_page:markets", None),
    ("telugu lo chupinchu", "te", "language", [], "assistant.set_language:te", "te"),
    ("schemes open chey", "te", "navigate", [], "navigation.open_page:schemes", None),
    ("assistant open chey", "te", "navigate", [], "navigation.open_page:ai-assistant", None),
    ("dashboard kholo", "te", "navigate", [], "navigation.open_page:dashboard", None),
    ("మార్కెట్ తెరువు", "te", "navigate", [], "navigation.open_page:markets", None),
    ("hindi mein dikhao", "te", "language", [], "assistant.set_language:hi", "hi"),
    # Hindi + transliteration (10)
    ("मंडी खोलो", "hi", "navigate", [], "navigation.open_page:markets", None),
    ("मौसम खोलो", "hi", "navigate", [], "navigation.open_page:weather", None),
    ("हिंदी में दिखाओ", "hi", "language", [], "assistant.set_language:hi", "hi"),
    ("बाज़ार खोलो", "hi", "navigate", [], "navigation.open_page:markets", None),
    ("तेलुगु में दिखाओ", "hi", "language", [], "assistant.set_language:te", "te"),
    ("mandi kholo", "hi", "navigate", [], "navigation.open_page:markets", None),
    ("yojana kholo", "hi", "navigate", [], "navigation.open_page:schemes", None),
    ("chat kholo", "hi", "navigate", [], "navigation.open_page:ai-assistant", None),
    ("disease kholo", "hi", "navigate", [], "navigation.open_page:disease-detection", None),
    ("analytics kholo", "hi", "navigate", [], "navigation.open_page:analytics", None),
]


def _sig(actions):
    out = []
    for a in actions:
        action, payload = a["action"], a["payload"]
        if action == "navigation.open_page":
            out.append(f"navigation.open_page:{payload.get('page')}")
        elif action == "assistant.set_language":
            out.append(f"assistant.set_language:{payload.get('language')}")
        else:
            out.append(action)
    return out


def test_golden_set_size():
    en = [c for c in CASES if c[1] == "en"]
    te = [c for c in CASES if c[1] == "te"]
    hi = [c for c in CASES if c[1] == "hi"]
    assert len(en) == 10 and len(te) == 10 and len(hi) == 10


def test_golden_commands():
    failures = []
    for text, lang, intent, tools, expected_action, expected_lang in CASES:
        sig = _sig(command_actions(text))
        if expected_action is None:
            if sig:
                failures.append((text, f"expected no action, got {sig}"))
        elif expected_action not in sig:
            failures.append((text, f"expected {expected_action}, got {sig}"))
    assert not failures, failures


def test_commands_never_emit_unsafe():
    from services.assistant.ui_actions import validate_ui_actions

    for text, lang, intent, tools, expected_action, expected_lang in CASES:
        for a in validate_ui_actions(command_actions(text)):
            assert a.action in ("navigation.open_page", "assistant.set_language")
            if a.action == "navigation.open_page":
                assert a.payload["page"] in (
                    "dashboard", "markets", "weather", "disease-detection",
                    "schemes", "analytics", "maps", "ai-assistant",
                )
