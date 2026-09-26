"""Shared emitter for hand-written locale catalogs.

Validates a translation dict against en.json (identical key sets,
non-empty values, placeholder preservation) and writes
frontend/i18n/messages/<code>.json on success. Any failure raises
before touching the catalog.
"""
import json
import re
import sys
from pathlib import Path

VAR_RE = re.compile(r"\{[a-zA-Z0-9_]+\}")
ROOT = Path(__file__).resolve().parents[1]
EN = json.loads((ROOT / "i18n" / "messages" / "en.json").read_text(encoding="utf-8"))
EN_KEYS = {f"{ns}.{k}" for ns, sec in EN.items() for k in sec}


def emit(code: str, t: dict) -> None:
    keys = {f"{ns}.{k}" for ns, sec in t.items() for k in sec}
    missing = EN_KEYS - keys
    extra = keys - EN_KEYS
    if missing:
        raise SystemExit(f"{code}: {len(missing)} missing keys: {sorted(missing)[:10]}")
    if extra:
        raise SystemExit(f"{code}: {len(extra)} extra keys: {sorted(extra)[:10]}")
    bad = []
    for ns, sec in t.items():
        for k, v in sec.items():
            if not isinstance(v, str) or not v.strip():
                bad.append(f"{ns}.{k} (empty)")
                continue
            if sorted(set(VAR_RE.findall(v))) != sorted(
                    set(VAR_RE.findall(EN[ns][k]))):
                bad.append(f"{ns}.{k} (placeholders: en={sorted(set(VAR_RE.findall(EN[ns][k])))} got={sorted(set(VAR_RE.findall(v)))})")
    if bad:
        raise SystemExit(f"{code}: {len(bad)} bad values:\n" + "\n".join(bad[:15]))
    out = ROOT / "i18n" / "messages" / f"{code}.json"
    out.write_text(json.dumps(t, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{code}: wrote {len(keys)} keys OK")


if __name__ == "__main__":
    print("import emit(code, translations) from a tr-XX script")
