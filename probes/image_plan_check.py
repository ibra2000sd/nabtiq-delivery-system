#!/usr/bin/env python3
"""image_plan_check — deterministic checks on the image-manifest (Wave 3 planning/asset layer).

This is the STATIC, dependency-free half of visual reliability: it validates the PLAN and the
ASSETS before any browser runs. The runtime frame-level first-paint check (light/dark, cold/warm
cache, slow network, no-JS, IO-missing/dead, post-wait visibility, zero-SVG-request) is a
CONTROLLED HYBRID browser probe — see probes/first_paint_probe.mjs — and runs against a BUILT
candidate in Wave 4. Keeping them separate is the honest split (Rev 2.2 §G.2).

Blocks (the Golden-Tur visual failures, caught at plan time):
  * SVG fallback where prohibited (first-paint SVG-before-raster flash risk) -> assert no svg fallback
  * a `documentary` slot with no real `documentary_source` (fake facility/cert risk)
  * a referenced asset file that is MISSING under the project (IO-missing)
  * an incomplete slot (missing required plan fields)
  * missing Light OR Dark variant (theme inconsistency)
  * focal_point out of the [0,1] range
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

REQUIRED = ["slot_id", "page", "section", "why_needed", "narrative_function", "subject",
            "desktop_crop", "mobile_crop", "focal_point", "light_variant", "dark_variant",
            "truth_label", "fallback", "alt_en", "alt_ar", "loading_priority", "status"]
ALLOWED_FALLBACK = {"raster", "lqip", "blurhash", "none"}   # NOT "svg"
ALLOWED_TRUTH = {"conceptual", "documentary"}

def main():
    proj = project_dir(sys.argv)
    rep = Report("image_plan_check")
    path = proj / "image-manifest.json"
    if not path.exists():
        print("  ℹ️  no image-manifest.json — no visual plan to check for this project (ok if text-only).")
        rep.print(); return rep.exit_code()
    doc = load_json(path)
    slots = doc.get("slots", [])
    if not slots:
        rep.add(FAIL, "image-manifest.json", "manifest present but declares no slots")
    for s in slots:
        sid = s.get("slot_id", "?")
        for f in REQUIRED:
            if f not in s:
                rep.add(FAIL, sid, f"missing plan field '{f}' (incomplete image plan)")
        # SVG-fallback prohibition (static analog of 'assert zero SVG requests')
        fb = s.get("fallback")
        if fb == "svg":
            rep.add(BLOCKED, sid, "SVG fallback prohibited — first-paint SVG-before-raster flash risk; use lqip/blurhash/raster")
        elif fb is not None and fb not in ALLOWED_FALLBACK:
            rep.add(FAIL, sid, f"invalid fallback {fb!r} (allowed: {sorted(ALLOWED_FALLBACK)})")
        # documentary must have a real source
        tl = s.get("truth_label")
        if tl == "documentary" and not s.get("documentary_source"):
            rep.add(BLOCKED, sid, "documentary slot has no documentary_source — refuse fake facility/certificate/staff")
        elif tl is not None and tl not in ALLOWED_TRUTH:
            rep.add(FAIL, sid, f"invalid truth_label {tl!r}")
        # theme completeness
        if s.get("light_variant") is not True or s.get("dark_variant") is not True:
            rep.add(FAIL, sid, "missing Light or Dark variant (theme inconsistency)")
        # focal point range
        fp = s.get("focal_point")
        if isinstance(fp, list) and len(fp) == 2:
            if not all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in fp):
                rep.add(FAIL, sid, f"focal_point out of [0,1] range: {fp}")
        # asset presence (IO-missing)
        asset = s.get("asset")
        if asset and not (str(asset).startswith("http://") or str(asset).startswith("https://")):
            if not (proj / asset).exists():
                rep.add(BLOCKED, sid, f"asset MISSING under project (IO-missing): {asset}")
    print("  ℹ️  static plan/asset check. Runtime frame-level first-paint (light/dark, cold/warm cache,")
    print("      slow network, no-JS, IO-missing/dead, post-wait) is the CONTROLLED-HYBRID browser probe")
    print("      probes/first_paint_probe.mjs — it runs against a BUILT candidate in Wave 4.")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
