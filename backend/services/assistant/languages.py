"""Canonical language registry (V1.3 §3). Single source of truth.

Every subsystem (capabilities, ASR/TTS reporting, frontend locale store,
validation) consumes THIS list. Capability flags reflect the ACTUAL
runtime — never claim support that is not installed and verified:

- ui_translation_available: a shipped message catalog exists.
- asr_available / tts_available: engine installed AND language verified.
- translation_available: runtime MT path (IndicTrans2) deployed.
- assistant_available: LLM path accepts the language.
"""

from __future__ import annotations

from pydantic import BaseModel


class LanguageDefinition(BaseModel):
    code: str  # stable short code: en, te, hi ...
    locale: str  # BCP-47 for Intl/format APIs: en-IN, te-IN ...
    english_name: str
    native_name: str
    script: str
    rtl: bool = False
    ui_translation_available: bool = False
    asr_available: bool = False
    tts_available: bool = False
    translation_available: bool = False
    assistant_available: bool = True


# code, locale, english, native, script, rtl
_SPECS: list[tuple] = [
    ("en", "en-IN", "English", "English", "Latin", False),
    ("as", "as-IN", "Assamese", "অসমীয়া", "Bengali", False),
    ("bn", "bn-IN", "Bengali", "বাংলা", "Bengali", False),
    ("brx", "brx-IN", "Bodo", "बड़ो", "Devanagari", False),
    ("doi", "doi-IN", "Dogri", "डोगरी", "Devanagari", False),
    ("gu", "gu-IN", "Gujarati", "ગુજરાતી", "Gujarati", False),
    ("hi", "hi-IN", "Hindi", "हिन्दी", "Devanagari", False),
    ("kn", "kn-IN", "Kannada", "ಕನ್ನಡ", "Kannada", False),
    ("ks", "ks-IN", "Kashmiri", "کٲشُر", "Arabic", True),
    ("kok", "kok-IN", "Konkani", "कोंकणी", "Devanagari", False),
    ("mai", "mai-IN", "Maithili", "मैथिली", "Devanagari", False),
    ("ml", "ml-IN", "Malayalam", "മലയാളം", "Malayalam", False),
    ("mni", "mni-IN", "Manipuri", "মণিপুরী", "Bengali", False),
    ("mr", "mr-IN", "Marathi", "मराठी", "Devanagari", False),
    ("ne", "ne-IN", "Nepali", "नेपाली", "Devanagari", False),
    ("or", "or-IN", "Odia", "ଓଡ଼ିଆ", "Odia", False),
    ("pa", "pa-IN", "Punjabi", "ਪੰਜਾਬੀ", "Gurmukhi", False),
    ("sa", "sa-IN", "Sanskrit", "संस्कृतम्", "Devanagari", False),
    ("sat", "sat-IN", "Santali", "ᱥᱟᱱᱛᱟᱲᱤ", "Ol Chiki", False),
    ("sd", "sd-IN", "Sindhi", "سنڌي", "Arabic", True),
    ("ta", "ta-IN", "Tamil", "தமிழ்", "Tamil", False),
    ("te", "te-IN", "Telugu", "తెలుగు", "Telugu", False),
    ("ur", "ur-IN", "Urdu", "اردو", "Arabic", True),
]

# Locales with a shipped message catalog (frontend/i18n/messages/<code>.json).
_SHIPPED_CATALOGS = frozenset({"en", "te", "hi"})

LANGUAGES: list[LanguageDefinition] = [
    LanguageDefinition(
        code=code,
        locale=locale,
        english_name=english,
        native_name=native,
        script=script,
        rtl=rtl,
        ui_translation_available=(code in _SHIPPED_CATALOGS),
    )
    for code, locale, english, native, script, rtl in _SPECS
]

_BY_CODE: dict[str, LanguageDefinition] = {lang.code: lang for lang in LANGUAGES}


def get_language(code: str | None) -> LanguageDefinition | None:
    """Lookup by short code. Unknown codes return None (caller falls back)."""
    if not code:
        return None
    return _BY_CODE.get(code.strip().lower())


def resolve_language(code: str | None, default: str = "en") -> LanguageDefinition:
    """Always return a definition; unknown codes fall back to default."""
    return get_language(code) or _BY_CODE.get(default, LANGUAGES[0])


def language_matrix() -> list[dict]:
    """Safe capability matrix for the capabilities endpoint. No secrets."""
    return [lang.model_dump() for lang in LANGUAGES]
