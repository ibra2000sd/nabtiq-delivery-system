#!/usr/bin/env python3
"""header_csp_scan — baseline security headers + CSP shape (Rev 2.1 §F.1; class: HYBRID).

Presence/shape only. A green result does NOT prove the CSP has no exploitable gap — a human
confirms policy strength. Baseline is MANDATORY: a missing headers artifact BLOCKS.
Reads <proj>/security/headers.json.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

REQUIRED = ["Content-Security-Policy", "Strict-Transport-Security",
            "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]

def main():
    proj = project_dir(sys.argv)
    rep = Report("header_csp_scan")
    path = proj / "security" / "headers.json"
    if not path.exists():
        rep.add(BLOCKED, "security/headers.json",
                "missing — baseline security headers are MANDATORY in every profile")
        rep.print(); return rep.exit_code()
    doc = load_json(path)
    headers = {k.lower(): v for k, v in doc.get("headers", {}).items()}
    for h in REQUIRED:
        if h.lower() not in headers:
            rep.add(BLOCKED, "security/headers.json", f"missing required header: {h}")
    csp = headers.get("content-security-policy", "")
    if csp:
        if "unsafe-inline" in csp and ("script-src" in csp or "default-src" in csp):
            rep.add(FAIL, "CSP", "script context allows 'unsafe-inline' — remove it (nonces/hashes instead)")
        if "require-trusted-types-for" not in csp:
            rep.add(FAIL, "CSP", "no Trusted Types opt-in (require-trusted-types-for 'script') — recommended for DOM-XSS defense")
    print("  ℹ️  class=HYBRID: presence/shape checked; a human still confirms CSP strength (no probe proves 'no gap').")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
