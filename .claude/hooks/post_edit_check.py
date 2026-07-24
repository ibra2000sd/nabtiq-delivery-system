#!/usr/bin/env python3
"""PostToolUse hook — runs the relevant probe after an Edit/Write.

Claude Code passes hook input as JSON on STDIN (verified against code.claude.com/docs/en/hooks):
  { "hook_event_name": "PostToolUse", "tool_name": "Edit", "tool_input": { "file_path": "..." }, "cwd": "..." }
PostToolUse cannot block (per docs); this is an informational fast-feedback check. CI (.github/workflows)
is the hard gate. Exit 0 always; we print probe output so it appears in the transcript.
"""
import sys, json, subprocess, re
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    fp = (data.get("tool_input") or {}).get("file_path") or ""
    if not fp:
        return 0
    root = Path(__file__).resolve().parents[2]  # repo root (.claude/hooks/ -> repo)
    m = re.search(r"(projects/[^/]+)/", fp.replace("\\", "/"))
    if not m:
        return 0
    proj = root / m.group(1)
    if not proj.is_dir():
        return 0
    name = Path(fp).name
    probes = []
    if name == "truth-ledger.json":
        subprocess.run([sys.executable, str(root / "scripts" / "seal.py"), fp],
                       cwd=root, capture_output=True)
        probes = ["truth_ledger_lint"]
    elif name.endswith(".content.json"):
        probes = ["content_lint", "bilingual_parity_check"]
    elif "/security/" in fp.replace("\\", "/"):
        probes = ["secrets_scan", "header_csp_scan", "privacy_scan", "sca_triage"]
    for p in probes:
        r = subprocess.run([sys.executable, str(root / "probes" / f"{p}.py"), str(proj)],
                           cwd=root, capture_output=True, text=True)
        sys.stdout.write(r.stdout)
    return 0

if __name__ == "__main__":
    sys.exit(main())
