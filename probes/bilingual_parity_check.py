#!/usr/bin/env python3
"""bilingual_parity_check — enforce EN/AR parity of FACTS, not literal equivalence (Rev 2.1 §E.3).

For each product/service page that carries locales:
  * both `locales.en` and `locales.ar` must exist with non-empty blocks;
  * the set of `claim_refs` (fact ids referenced) must be IDENTICAL across locales — a fact present
    in one locale but not the other is a parity failure (BLOCK): it means an unauthorized divergence
    (a claim added to one language, or dropped from the other). Parity = same facts, NOT same words.
Class: deterministic (set comparison). Native fluency is judged by the arabic-native reviewer agent,
never by this probe.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

def main():
    proj = project_dir(sys.argv)
    rep = Report("bilingual_parity_check")
    pages = sorted((proj / "pages").glob("*.content.json")) if (proj / "pages").is_dir() else []
    checked = 0
    for pg in pages:
        doc = load_json(pg)
        if doc.get("page_type") not in ("product", "service"):
            continue
        loc = doc.get("locales")
        if not loc:
            continue  # a page may be single-language by design; only enforce parity when locales are declared
        checked += 1
        en, ar = loc.get("en"), loc.get("ar")
        for lname, l in (("en", en), ("ar", ar)):
            if not l or not l.get("blocks"):
                rep.add(BLOCKED, f"{pg.name}:{lname}", f"missing or empty {lname} locale content")
        if en and ar:
            en_refs = set(en.get("claim_refs", []))
            ar_refs = set(ar.get("claim_refs", []))
            only_en = en_refs - ar_refs
            only_ar = ar_refs - en_refs
            if only_en:
                rep.add(BLOCKED, f"{pg.name}", f"facts in EN but NOT in AR: {sorted(only_en)} (parity failure)")
            if only_ar:
                rep.add(BLOCKED, f"{pg.name}", f"facts in AR but NOT in EN: {sorted(only_ar)} (parity failure)")
    if checked == 0:
        print("  ℹ️  no bilingual product/service pages declared locales — nothing to check.")
    print("  ℹ️  parity = same FACTS across locales; native Arabic FLUENCY is judged by the arabic-native reviewer agent, not here.")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
