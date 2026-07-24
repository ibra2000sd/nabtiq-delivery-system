"""Shared helpers for Nabtiq validation/evidence probes.

Zero external dependencies (Python 3.8+ stdlib only) so probes run locally,
in Claude Code hooks, and in GitHub Actions without an install step.
"""
import json, hashlib, sys, io
from pathlib import Path

# ---- result model -------------------------------------------------------
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"

class Finding:
    def __init__(self, level, where, message):
        self.level = level      # FAIL | BLOCKED
        self.where = where
        self.message = message
    def __str__(self):
        icon = "⛔" if self.level == BLOCKED else "❌"
        return f"  {icon} [{self.level}] {self.where}: {self.message}"

class Report:
    def __init__(self, probe):
        self.probe = probe
        self.findings = []
    def add(self, level, where, message):
        self.findings.append(Finding(level, where, message))
    @property
    def verdict(self):
        if any(f.level == BLOCKED for f in self.findings):
            return BLOCKED
        if any(f.level == FAIL for f in self.findings):
            return FAIL
        return PASS
    def print(self):
        v = self.verdict
        icon = "✅" if v == PASS else ("⛔" if v == BLOCKED else "❌")
        print(f"{icon} {self.probe}: {v}")
        for f in self.findings:
            print(f)
    def exit_code(self):
        return 0 if self.verdict == PASS else 1

# ---- canonical hashing (matches scripts/seal.py) ------------------------
def canonical(obj):
    """Deterministic JSON for hashing: sorted keys, compact, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def content_hash(payload):
    return "sha256:" + hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()

def hash_of_artifact(doc):
    """Hash an artifact's bytes EXCLUDING its own content_hash field."""
    d = dict(doc)
    d.pop("content_hash", None)
    return content_hash(d)

# ---- io -----------------------------------------------------------------
def load_json(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def project_dir(argv):
    if len(argv) < 2:
        print("usage: <probe>.py <project-dir>", file=sys.stderr)
        sys.exit(2)
    p = Path(argv[1])
    if not p.is_dir():
        print(f"not a directory: {p}", file=sys.stderr)
        sys.exit(2)
    return p
