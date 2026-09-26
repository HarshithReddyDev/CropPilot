"""Find t("ns.key") usages with no matching en.json entry (would render
as a raw key). Excludes dynamic keys built via concatenation."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
en = json.load(open(ROOT / "i18n" / "messages" / "en.json", encoding="utf-8"))
have = {f"{ns}.{k}" for ns, sec in en.items() for k in sec}

used: dict[str, list[str]] = {}
for p in list((ROOT / "app").rglob("*.tsx")) + list((ROOT / "components").rglob("*.tsx")):
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in re.finditer(r"""\bt\(\s*["']([a-z0-9_]+\.[A-Za-z0-9_]+)["']""", text):
        used.setdefault(m.group(1), []).append(f"{p.relative_to(ROOT)}")

missing = {k: v for k, v in used.items() if k not in have}
print(f"static t() keys used: {len(used)}; missing from en.json: {len(missing)}")
for k, locs in sorted(missing.items()):
    print(f"  {k}  ({locs[0]}{f' +{len(locs)-1}' if len(locs) > 1 else ''})")
