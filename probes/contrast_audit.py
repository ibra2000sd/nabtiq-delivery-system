#!/usr/bin/env python3
"""contrast_audit — WCAG contrast (Rev 2.2 §G.3): DETERMINISTIC for solid/computed colors,
HYBRID/human for text over imagery/translucency/complex backgrounds.

Reads <proj>/design-tokens.json -> `contrast_pairs`: [{name, fg, bg, over_image, large_text?}].
  * solid pair (over_image=false): compute the ratio; BLOCK if < 4.5 (AA normal) / < 3.0 (AA large).
    A validated parser — rejects impossible values (ratios are clamped to [1, 21]).
  * over_image / translucent pair (over_image=true): FLAG as hybrid — a human (or worst-case sampling)
    must judge; a single computed ratio is not meaningful over an image.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def luminance(hex_):
    h = hex_.lstrip("#")
    if len(h) == 3: h = "".join(ch * 2 for ch in h)
    if len(h) != 6: return None
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def ratio(fg, bg):
    lf, lb = luminance(fg), luminance(bg)
    if lf is None or lb is None: return None
    hi, lo = max(lf, lb), min(lf, lb)
    r = (hi + 0.05) / (lo + 0.05)
    return max(1.0, min(21.0, r))  # validated: impossible values clamped

def main():
    proj = project_dir(sys.argv)
    rep = Report("contrast_audit")
    path = proj / "design-tokens.json"
    if not path.exists():
        print("  ℹ️  no design-tokens.json — no declared contrast pairs to check.")
        rep.print(); return rep.exit_code()
    pairs = load_json(path).get("contrast_pairs", [])
    hybrid = 0
    for p in pairs:
        name = p.get("name", "?")
        if p.get("over_image") or p.get("translucent"):
            hybrid += 1
            continue  # hybrid: human judges text-over-image; a probe cannot prove it
        r = ratio(p.get("fg", ""), p.get("bg", ""))
        if r is None:
            rep.add(FAIL, name, f"invalid colour(s): fg={p.get('fg')} bg={p.get('bg')}")
            continue
        need = 3.0 if p.get("large_text") else 4.5
        if r < need:
            rep.add(BLOCKED, name, f"contrast {r:.2f}:1 < {need}:1 (WCAG 2.2 AA) for {p.get('fg')} on {p.get('bg')}")
    if hybrid:
        print(f"  ℹ️  {hybrid} text-over-image/translucent pair(s) FLAGGED as HYBRID — human/worst-case review required (not auto-passed).")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
