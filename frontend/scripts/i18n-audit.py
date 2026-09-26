"""i18n hardcoded-string audit (read-only).

Scans frontend .tsx/.ts for likely user-visible English strings NOT routed
through t():
  - JSX text nodes containing 2+ letter words
  - placeholder=/aria-label=/title= string literals with English text
  - toast()/sonner/alert() literal messages
  - hardcoded toLocaleString("en-IN") / manual month names
Ignores: className, URLs/imports, CSS, technical IDs, query params, test/e2e.
Outputs a ranked file list + sample hits. Exit 0 always (informational).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = [ROOT / "app", ROOT / "components", ROOT / "hooks",
        ROOT / "services", ROOT / "lib", ROOT / "stores", ROOT / "providers"]

SKIP_DIRS = {"test-results", ".next", "node_modules"}
SKIP_FILES = re.compile(r"\.(spec|test)\.(ts|tsx)$")

CSS_HINT = re.compile(r"(className|tw-|flex|grid|rounded|bg-|text-|px-|py-|border|shadow|animate|dark:|hover:|focus:|ring-|outline-|cursor-|transition|duration|ease|scale|rotate|translate|opacity|z-|top-|left-|w-|h-|max-|min-|overflow|items-|justify|gap-|space-|font-|leading|tracking)")
URL_HINT = re.compile(r"(https?://|/|@/|api/|_next|mailto:|tel:|\.json|\.css|\.tsx?|\.ico|\.png|\.svg)")
TECH_HINT = re.compile(r"(?i)^(mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*$|^[A-Z0-9_/\-]{2,}$|^\d|SELECT|FROM|WHERE|px$|rem$|ms$|#[0-9a-f]{3,8}")


def is_english_text(s: str) -> bool:
    words = re.findall(r"[A-Za-z]{2,}", s)
    return len(words) >= 1 and len(s.strip()) >= 3


def check_file(path: Path):
    hits = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return hits
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith(("import ", "export ", "//", "*", "/*", "}")):
            continue
        # JSX text nodes: >Some Text<
        for m in re.finditer(r">([^<>{}]+)<", line):
            txt = m.group(1).strip()
            if len(txt) >= 4 and is_english_text(txt) and not CSS_HINT.search(txt) \
                    and not URL_HINT.search(txt) and not txt.startswith(("{", "$", "<")):
                if TECH_HINT.search(txt):
                    continue
                hits.append((i, "jsx-text", txt[:90]))
        # JSX string attrs with user text
        for m in re.finditer(r'(placeholder|aria-label|aria-describedby|title|alt|label)="([^"]+)"', line):
            txt = m.group(2)
            if is_english_text(txt) and not URL_HINT.search(txt):
                hits.append((i, f"attr-{m.group(1)}", txt[:90]))
        # toast / alert / Error literals
        for m in re.finditer(r'(toast\.(?:success|error|info|warning|loading)?\(?["\'])([^"\']{4,})["\']', line):
            hits.append((i, "toast", m.group(2)[:90]))
        if re.search(r'\balert\s*\(', line):
            hits.append((i, "alert", s[:90]))
        # hardcoded locale formatting
        if 'toLocaleString("en-IN")' in line or "toLocaleString('en-IN')" in line:
            hits.append((i, "hard-locale", s[:90]))
    return hits


def main():
    files = {}
    for base in SCAN:
        if not base.exists():
            continue
        for p in base.rglob("*.tsx"):
            if SKIP_FILES.search(p.name) or any(d in p.parts for d in SKIP_DIRS):
                continue
            h = check_file(p)
            if h:
                files[str(p.relative_to(ROOT))] = h
        for p in base.rglob("*.ts"):
            if p.name.endswith(".d.ts") or SKIP_FILES.search(p.name):
                continue
            if any(d in p.parts for d in SKIP_DIRS):
                continue
            h = check_file(p)
            if h:
                files[str(p.relative_to(ROOT))] = h
    total = sum(len(v) for v in files.values())
    print(f"files with likely hardcoded strings: {len(files)}; total hits: {total}")
    ranked = sorted(files.items(), key=lambda kv: -len(kv[1]))[:25]
    def safe(s: str) -> str:
        return s.encode("ascii", "replace").decode()
    for f, hits in ranked:
        print(safe(f"\n{f} ({len(hits)})"))
        for ln, kind, txt in hits[:8]:
            print(safe(f"  L{ln} [{kind}] {txt}"))
    out = Path(__file__).parent / "i18n-audit-report.json"
    out.write_text(json.dumps(files, indent=1), encoding="utf-8")
    print(f"\nfull report: {out}")


if __name__ == "__main__":
    main()
