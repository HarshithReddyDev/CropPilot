"""Deterministic command intents (V1.3 §26-28).

Voice/text commands like "Switch to Telugu" or "Open markets" are
command-shaped: a small deterministic matcher beats the LLM on
reliability (no hallucinated routes, no invented language codes).
Matched commands emit validated UI actions ALONGSIDE the normal LLM
answer — the agent still responds conversationally.

Only allow-listed pages (ui_actions.ALLOWED_PAGES) and registry language
codes (languages.get_language) can ever be emitted.
"""

from __future__ import annotations

import re

from services.assistant.languages import LANGUAGES, get_language
from services.assistant.ui_actions import ALLOWED_PAGES

# "switch/change/show in ..." across en + hi/te transliteration.
_SWITCH_RES = [
    re.compile(r"\bswitch\b.*\bto\b", re.IGNORECASE),
    re.compile(r"\bchange\b.*\blanguage\b", re.IGNORECASE),
    re.compile(r"\bbhasha\b", re.IGNORECASE),
    re.compile(r"भाषा", re.IGNORECASE),
    re.compile(r"భాష", re.IGNORECASE),
    re.compile(r"\bmein\b.*\bdikhao\b", re.IGNORECASE),
    re.compile(r"\blo\b.*\bchupinchu\b", re.IGNORECASE),
    re.compile(r"में\s*दिखाओ", re.IGNORECASE),
    re.compile(r"కు\s*మార్చు", re.IGNORECASE),
]

# "open/go to ..." across en + hi/te transliteration.
_NAV_RES = [
    re.compile(r"\bopen\b", re.IGNORECASE),
    re.compile(r"\bgo\s*to\b", re.IGNORECASE),
    re.compile(r"\bnavigate\b", re.IGNORECASE),
    re.compile(r"\bkhol", re.IGNORECASE),
    re.compile(r"खोल", re.IGNORECASE),
    re.compile(r"తెరువు", re.IGNORECASE),
]

# Spoken page names -> allow-listed page ids.
_PAGE_ALIASES: dict[str, str] = {
    "dashboard": "dashboard",
    "market": "markets",
    "markets": "markets",
    "mandi": "markets",
    "मंडी": "markets",
    "bazaar": "markets",
    "बाजार": "markets",
    "बाज़ार": "markets",
    "మార్కెట్": "markets",
    "weather": "weather",
    "mausam": "weather",
    "मौसम": "weather",
    "వాతావరణ": "weather",
    "disease": "disease-detection",
    "detection": "disease-detection",
    "rog": "disease-detection",
    "रोग": "disease-detection",
    "రోగ": "disease-detection",
    "scheme": "schemes",
    "schemes": "schemes",
    "yojana": "schemes",
    "योजना": "schemes",
    "పథక": "schemes",
    "analytics": "analytics",
    "map": "maps",
    "maps": "maps",
    "assistant": "ai-assistant",
    "chat": "ai-assistant",
    "bot": "ai-assistant",
}


#: Common spelling variants the registry's canonical native names miss
#: (anusvara/nukta/script variants real users type). Checked before the
#: registry loop; registry codes always win on exact match first.
_LANG_ALIASES: dict[str, str] = {
    "हिंदी": "hi",
    "तेलुगु": "te",
}


def _language_mentioned(text: str) -> str | None:
    """Registry language code named in the text, or None."""
    lowered = f" {text.lower()} "
    for lang in LANGUAGES:
        for needle in (lang.english_name.lower(), lang.native_name.lower(), lang.code):
            if not needle:
                continue
            padded = f" {needle} " in lowered.replace("ـ", " ")
            # Agglutinative suffixes ("తెలుగుకు", "हिंदीमें"): names longer
            # than 2 chars may attach case endings; 2-letter codes stay
            # word-boundaried to avoid false hits ("state" has "te").
            prefixed = len(needle) > 2 and f" {needle}" in lowered
            if (padded or prefixed) and get_language(lang.code) is not None:
                return lang.code
    for variant, code in _LANG_ALIASES.items():
        if variant.lower() in lowered and get_language(code) is not None:
            return code
    return None


def match_language_switch(text: str) -> str | None:
    """Language code for a switch-command, or None (not a command)."""
    if not any(rx.search(text) for rx in _SWITCH_RES):
        return None
    return _language_mentioned(text)


def match_open_page(text: str) -> str | None:
    """Allow-listed page id for an open-command, or None."""
    if not any(rx.search(text) for rx in _NAV_RES):
        return None
    lowered = text.lower()
    for alias, page in _PAGE_ALIASES.items():
        if alias in lowered and page in ALLOWED_PAGES:
            return page
    return None


def command_actions(text: str) -> list[dict]:
    """Validated UI actions for deterministic commands (may be empty)."""
    actions: list[dict] = []
    lang = match_language_switch(text)
    if lang:
        actions.append({"action": "assistant.set_language", "payload": {"language": lang}})
    page = match_open_page(text)
    if page:
        actions.append({"action": "navigation.open_page", "payload": {"page": page}})
    return actions
