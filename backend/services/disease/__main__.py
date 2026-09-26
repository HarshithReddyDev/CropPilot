"""Registry CLI: validate | coverage.

Usage:
  python -m services.disease.registry validate
  python -m services.disease.registry coverage
"""

from __future__ import annotations

import sys


def cmd_validate() -> int:
    from services.disease.registry import validate_registry

    errors, warnings = validate_registry()
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        return 1
    print("VALID: registry passes production gates")
    return 0


def cmd_coverage() -> int:
    from services.disease import registry as registry_mod
    from services.disease import taxonomy as taxonomy_mod

    diseases = taxonomy_mod.all_diseases()
    prod = registry_mod.production_models()
    covered: set[str] = set()
    for m in prod:
        dis = m.diseases
        if isinstance(dis, list):
            covered.update(dis)
        elif dis == "plantvillage_multicrop":
            covered.update([d["id"] for d in diseases if d["id"].startswith("plantvillage.")])
        elif isinstance(dis, str) and dis.endswith("_multidisease"):
            crop = dis.split("_")[0]
            covered.update([d["id"] for d in diseases if d.get("crop") == crop])

    def _pct(a: int, b: int) -> str:
        return f"{100.0 * a / b:.1f}%" if b else "n/a"

    total = len(diseases)
    research = [m for m in registry_mod.research_models() if m.research_only]
    research_cov: set[str] = set()
    for m in research:
        if isinstance(m.diseases, list):
            research_cov.update(m.diseases)
    india = [d for d in diseases if d.get("india") == "high"]
    tel = [d for d in diseases if d.get("telangana") == "high"]
    print(f"taxonomy diseases: {total}")
    print(f"production-enabled disease rows: {len(covered)} ({_pct(len(covered), total)})")
    print(f"research-only disease rows: {len(research_cov)}")
    print(f"no-model rows: {total - len(covered | research_cov)} (coverage_status=requires_training)")
    print(f"india-high covered: {len([d for d in india if d['id'] in covered])}/{len(india)}")
    print(f"india-high uncovered: {[d['id'] for d in india if d['id'] not in covered]}")
    print(f"telangana-high covered: {len([d for d in tel if d['id'] in covered])}/{len(tel)}")
    print(f"telangana-high uncovered: {[d['id'] for d in tel if d['id'] not in covered]}")
    print("NOTE: taxonomy rows != runnable models. Only production-enabled rows diagnose.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "validate":
        return cmd_validate()
    if len(argv) >= 2 and argv[1] == "coverage":
        return cmd_coverage()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
