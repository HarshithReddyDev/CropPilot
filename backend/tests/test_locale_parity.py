"""Backend/frontend locale parity (V1.3 §3). The two registries must
agree on codes, names, scripts, and RTL flags."""

from services.assistant.languages import LANGUAGES

# Mirror of frontend/lib/languages.ts LOCALES (code, locale, english,
# native, script, rtl). Update both files together.
FRONTEND_LOCALES = [
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


def test_locale_parity():
    assert len(LANGUAGES) == 23 == len(FRONTEND_LOCALES)
    for lang, front in zip(LANGUAGES, FRONTEND_LOCALES):
        code, locale, english, native, script, rtl = front
        assert lang.code == code, code
        assert lang.locale == locale, code
        assert lang.english_name == english, code
        assert lang.native_name == native, code
        assert lang.script == script, code
        assert lang.rtl == rtl, code
