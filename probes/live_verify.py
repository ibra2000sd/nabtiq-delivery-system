#!/usr/bin/env python3
"""live_verify — post-deploy verification on the REAL production path (Rev 2.1 §J.2 step 8).
Stage-aware: skips if there is no live-verify.json.

Blocks when a live-verify report exists but:
  * target_url is localhost/127.0.0.1/file:// (tested a local server, not production — the Golden-Tur
    'tested an old local server' failure)
  * any route health check failed
  * first-paint-on-production is not 'pass'
  * secure headers were not re-scanned OK on the live origin
This is EVIDENCE for the human live-visual + indexing approval events — not the approval itself.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, load_json, project_dir

def main():
    proj = project_dir(sys.argv)
    rep = Report("live_verify")
    path = proj / "live-verify.json"
    if not path.exists():
        print("  ℹ️  no live-verify.json — not deployed/verified yet (skip).")
        rep.print(); return rep.exit_code()
    d = load_json(path)
    url = (d.get("target_url") or "").lower()
    if (not url) or "localhost" in url or "127.0.0.1" in url or url.startswith("file://"):
        rep.add(BLOCKED, "live", f"target_url is not a real production URL ({d.get('target_url')!r}) — refuse to verify localhost")
    if d.get("routes_ok") is not True:
        rep.add(BLOCKED, "live", "one or more live route health checks failed")
    if d.get("first_paint_live") != "pass":
        rep.add(BLOCKED, "live", f"live first-paint not passing ({d.get('first_paint_live')!r})")
    if d.get("headers_ok") is not True:
        rep.add(BLOCKED, "live", "secure headers not re-scanned OK on the live origin")
    print("  ℹ️  live evidence for the human live-visual + indexing approval events (not the approval itself).")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
