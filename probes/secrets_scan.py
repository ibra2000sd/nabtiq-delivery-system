#!/usr/bin/env python3
"""secrets_scan — DETERMINISTIC detection of exposed secrets in a project subtree.

Any hit is BLOCKED. Class: deterministic detection (a match is authoritative; absence of a
match is NOT proof there are no secrets — it proves these patterns did not match).
"""
import sys, re
from pathlib import Path
from lib_common import Report, BLOCKED, project_dir

PATTERNS = [
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("generic secret assignment",
     re.compile(r"(?i)(?:aws_secret_access_key|api[_-]?key|secret[_-]?key|client[_-]?secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=_\-]{16,}")),
]
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".pdf", ".zip", ".pyc")

def main():
    proj = project_dir(sys.argv)
    rep = Report("secrets_scan")
    for p in proj.rglob("*"):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIX:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, pat in PATTERNS:
            m = pat.search(text)
            if m:
                snippet = m.group(0)[:12] + "…"
                rep.add(BLOCKED, str(p.relative_to(proj)), f"exposed secret ({label}): {snippet}")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
