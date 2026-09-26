"""Deterministic locale catalog generator (V1.3 §2/§52).

Syncs frontend/i18n/messages/<code>.json from the canonical en.json
using the IndicTrans2 runtime bridge. Deterministic: same en source +
same model = same output (greedy decoding, sorted keys).

Usage:
    python scripts/generate_catalogs.py --langs ta,bn,mr
    python scripts/generate_catalogs.py --all --check   # dry run

Structural validation (keys/placeholders) is enforced by
frontend/scripts/check-i18n.mjs afterwards. Generated files are
machine translations: spot-check agri terminology before release.
Requires cached IndicTrans2 weights; refuses to fabricate.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def _catalog_dir() -> Path:
    # Host checkout: <root>/frontend/... ; container: /app IS backend,
    # so the frontend tree is absent and generation must run on host.
    for base in (REPO, REPO.parent):
        candidate = base / "frontend" / "i18n" / "messages"
        if (candidate / "en.json").exists():
            return candidate
    raise SystemExit(
        "frontend/i18n/messages/en.json not found: run this script from "
        "a full repo checkout (not inside the api container)"
    )


CATALOG_DIR = _catalog_dir()


def flatten(obj: dict, prefix: str = "") -> list[tuple[str, str]]:
    out = []
    for key in sorted(obj):
        value = obj[key]
        if isinstance(value, dict):
            out.extend(flatten(value, f"{prefix}{key}."))
        else:
            out.append((f"{prefix}{key}", str(value)))
    return out


def unflatten(pairs: list[tuple[str, str]]) -> dict:
    root: dict = {}
    for dotted, value in pairs:
        node = root
        *parents, leaf = dotted.split(".")
        for part in parents:
            node = node.setdefault(part, {})
        node[leaf] = value
    return node


async def generate(lang: str, dry_run: bool = False) -> int:
    from services.assistant.languages import get_language
    from services.assistant.translation import translation_manager, TranslationUnavailable

    if get_language(lang) is None:
        print(f"SKIP {lang}: not in canonical registry")
        return 0
    if lang == "en":
        print("SKIP en: canonical source")
        return 0
    en = json.loads((CATALOG_DIR / "en.json").read_text(encoding="utf-8"))
    entries = flatten(en)
    target = CATALOG_DIR / f"{lang}.json"
    existing = {}
    if target.exists():
        existing = {k: v for k, v in flatten(json.loads(target.read_text(encoding="utf-8")))}
    missing = [(k, v) for k, v in entries if k not in existing]
    print(f"{lang}: {len(entries)} keys, {len(missing)} missing")
    if dry_run or not missing:
        return len(missing)
    translated: dict[str, str] = {}
    for key, value in missing:
        try:
            translated[key] = await translation_manager.translate(value, "en", lang)
        except TranslationUnavailable as e:
            print(f"ABORT {lang}: bridge unavailable ({e}); nothing written")
            return -1
    merged = {k: v for k, v in entries}
    merged.update(existing)
    merged.update(translated)
    target.write_text(json.dumps(unflatten(sorted(merged.items())),
                                 ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"WROTE {target} ({len(translated)} new)")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--langs", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    from services.assistant.languages import LANGUAGES

    if args.all:
        langs = [lang.code for lang in LANGUAGES if lang.code != "en"]
    else:
        langs = [c.strip().lower() for c in args.langs.split(",") if c.strip()]
    if not langs:
        print("nothing to do (pass --langs or --all)")
        return 0
    pending = 0
    for lang in langs:
        result = await generate(lang, dry_run=args.check)
        if result == -1:
            return 2
        pending += result
    print(f"missing keys remaining: {pending}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
