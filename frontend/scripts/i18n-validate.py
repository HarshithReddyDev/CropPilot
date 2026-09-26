"""i18n catalog validation (strict, exits nonzero on failure).

Checks across all 23 canonical locales:
  - catalog file exists and is valid JSON
  - identical key sets (namespace.key) vs en
  - no missing keys, no empty values
  - {placeholders} preserved exactly per key
  - script check: values contain the locale's native script, unless the
    value is placeholders/numbers/punctuation/preserved identifiers only
Usage: npm run i18n:validate  ->  python scripts/i18n-validate.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSG = ROOT / "i18n" / "messages"

LOCALES = ["en", "te", "hi", "ta", "bn", "mr", "gu", "kn", "ml", "pa",
           "as", "ne", "ur", "sa", "sd", "brx", "doi", "kok", "ks", "mai",
           "mni", "or", "sat"]

SCRIPT_RANGES = {
    "as": [(0x0980, 0x09FF)], "bn": [(0x0980, 0x09FF)],
    "mni": [(0x0980, 0x09FF)],
    "brx": [(0x0900, 0x097F)], "doi": [(0x0900, 0x097F)],
    "hi": [(0x0900, 0x097F)], "kok": [(0x0900, 0x097F)],
    "mai": [(0x0900, 0x097F)], "mr": [(0x0900, 0x097F)],
    "ne": [(0x0900, 0x097F)], "sa": [(0x0900, 0x097F)],
    "gu": [(0x0A80, 0x0AFF)], "pa": [(0x0A00, 0x0A7F)],
    "kn": [(0x0C80, 0x0CFF)], "ml": [(0x0D00, 0x0D7F)],
    "or": [(0x0B00, 0x0B7F)], "ta": [(0x0B80, 0x0BFF)],
    "te": [(0x0C00, 0x0C7F)],
    "ks": [(0x0600, 0x06FF)], "sd": [(0x0600, 0x06FF)],
    "ur": [(0x0600, 0x06FF)],
    "sat": [(0x1C50, 0x1C7F)],
    "en": [(0x0041, 0x007A)],
}

# Identifiers that must survive translation in Latin script.
PRESERVED = [
    "CropPilot", "Cropyaan", "AGMARKNET", "Open-Meteo", "IMD", "CGWB",
    "CWC", "SoilGrids", "GitHub", "Hugging Face", "DINOv2", "BioCLIP",
    "MobileNetV3", "Qwen", "LangGraph", "LangChain", "OpenRouter",
    "Ollama", "ONNX", "PostGIS", "MIT", "Apache-2.0", "OpenStreetMap",
    "Nominatim", "CARTO", "ERA5", "WMO",
]

VAR_RE = re.compile(r"\{[a-zA-Z0-9_]+\}")


def strip_neutral(text: str) -> str:
    t = VAR_RE.sub("", text)
    for p in PRESERVED:
        t = t.replace(p, "")
    # E-levels like E4, units, numbers, punctuation, whitespace, Latin alnum
    t = re.sub(r"[E][0-6]\b", "", t)
    t = re.sub(r"[0-9.,/%°+\-–—:;!?()\"'’‘₹$&@#*…™®©|…]", "", t)
    t = re.sub(r"[A-Za-z]", "", t)
    return t.strip(" \t\n")


def in_script(text: str, code: str) -> bool:
    ranges = SCRIPT_RANGES[code]
    # U+0964/0965 dandas are shared Indic punctuation (correct in Punjabi,
    # Gujarati prose etc.) — never count them as foreign script.
    return any(
        any(lo <= ord(c) <= hi for lo, hi in ranges)
        for c in text
        if c not in ("।", "॥")
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    catalogs: dict[str, dict] = {}
    for code in LOCALES:
        p = MSG / f"{code}.json"
        if not p.exists():
            errors.append(f"{code}: catalog missing")
            continue
        try:
            catalogs[code] = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{code}: invalid JSON ({e})")
    if "en" not in catalogs:
        print("FATAL: en.json missing/unparseable");
        return 2
    en_keys = {f"{ns}.{k}" for ns, sec in catalogs["en"].items() for k in sec}
    en_vars = {}
    for ns, sec in catalogs["en"].items():
        for k, v in sec.items():
            en_vars[f"{ns}.{k}"] = sorted(set(VAR_RE.findall(v or "")))
    for code, doc in catalogs.items():
        if code == "en":
            continue
        keys = {f"{ns}.{k}" for ns, sec in doc.items() for k in sec}
        for m in sorted(en_keys - keys):
            errors.append(f"{code}: missing key {m}")
        for x in sorted(keys - en_keys):
            errors.append(f"{code}: extra key {x} (not in en)")
        for ns, sec in doc.items():
            for k, v in sec.items():
                full = f"{ns}.{k}"
                if not isinstance(v, str) or not v.strip():
                    errors.append(f"{code}: empty value {full}")
                    continue
                if sorted(set(VAR_RE.findall(v))) != en_vars.get(full, []):
                    errors.append(
                        f"{code}: placeholder mismatch {full} "
                        f"(en={en_vars.get(full)}, got={sorted(set(VAR_RE.findall(v)))})")
                rest = strip_neutral(v)
                if rest and not in_script(v, code):
                    warnings.append(f"{code}: no native script {full} = {v[:60]!r}")
    print(f"locales checked: {len(catalogs)}/{len(LOCALES)}; en keys: {len(en_keys)}")
    print(f"errors: {len(errors)}; warnings: {len(warnings)}")
    for e in errors[:40]:
        print("ERROR " + e)
    for w in warnings[:40]:
        print("WARN " + w)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
