#!/usr/bin/env python3
"""content_lint — essential-field resolution + placeholder/empty checks (Rev 2.1 §E.2).

A product/service page's ESSENTIAL fields must each resolve to exactly one of:
  verified | owner-stated | approved-not-applicable | approved-omission | blocking-open-question
'unknown' (or a bare/empty value) is NOT an accepted resolution for an essential field.
A page with any essential field == 'blocking-open-question' (or unresolved) FAILS publication.
Also flags: empty headings, temporary/internal language.
"""
import sys, re
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

ACCEPTED = {"verified", "owner-stated", "approved-not-applicable", "approved-omission"}
BLOCKING = "blocking-open-question"
ESSENTIAL_PRODUCT = ["what_it_is", "applications", "sourcing_role", "documented_origin",
                     "quality_indicators", "packaging", "trade_terms", "logistics",
                     "documentation", "enquiry_requirements"]
TEMP_PATTERNS = [r"\blorem ipsum\b", r"\bTODO\b", r"\bTBD\b", r"\bplaceholder\b",
                 r"\binternal note\b", r"ملاحظة داخلية", r"مؤقّ?ت", r"XXX"]

def main():
    proj = project_dir(sys.argv)
    rep = Report("content_lint")
    pages = sorted((proj / "pages").glob("*.content.json")) if (proj / "pages").is_dir() else []
    if not pages:
        rep.add(FAIL, "pages/", "no *.content.json pages found")
        rep.print(); return rep.exit_code()

    for pg in pages:
        doc = load_json(pg)
        name = pg.name
        # empty heading / temp language across text blocks
        for b in doc.get("blocks", []):
            heading = (b.get("heading") or "").strip()
            body = (b.get("body") or "").strip()
            if heading and not body:
                rep.add(FAIL, f"{name}:{b.get('id','?')}", "heading with no body (empty section)")
            for txt in (heading, body):
                for pat in TEMP_PATTERNS:
                    if re.search(pat, txt, re.IGNORECASE):
                        rep.add(BLOCKED, f"{name}:{b.get('id','?')}", f"temporary/internal language found (/{pat}/)")

        # essential-field resolution for product/service pages
        if doc.get("page_type") in ("product", "service"):
            ef = doc.get("essential_fields", {})
            for field in ESSENTIAL_PRODUCT:
                res = ef.get(field)
                if res is None or res == "" or res == "unknown":
                    rep.add(BLOCKED, f"{name}:{field}",
                            "essential field unresolved ('unknown'/empty is not acceptable) — must be "
                            "verified/owner-stated/approved-not-applicable/approved-omission, or it blocks")
                elif res == BLOCKING:
                    rep.add(BLOCKED, f"{name}:{field}",
                            "essential field is a blocking-open-question — page cannot publish until resolved")
                elif res not in ACCEPTED:
                    rep.add(FAIL, f"{name}:{field}", f"invalid resolution {res!r}")

    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
