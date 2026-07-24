#!/usr/bin/env python3
"""sca_triage — SAST/SCA severity TRIAGE (Rev 2.2 §item 15; class: HYBRID + triage).

Raw scanner severity does NOT auto-block. The gate blocks ONLY on findings matching the block
policy: known-exploited (KEV), exposed-secret, confirmed, or accepted high-confidence. An
untriaged scanner "High" opens a triage task — it does not fail the build (prevents scanner
noise from blocking delivery while still hard-blocking real risk).
Reads <proj>/security/findings.json and <proj>/security/policy.json.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, load_json, project_dir

def blocks(f, policy):
    reasons = []
    if f.get("kev") and "kev" in policy: reasons.append("known-exploited (KEV)")
    if f.get("exposed_secret") and "exposed_secret" in policy: reasons.append("exposed secret")
    if f.get("status") == "confirmed" and "confirmed" in policy: reasons.append("confirmed finding")
    if f.get("status") == "accepted" and f.get("confidence") == "high" and "accepted-high-confidence" in policy:
        reasons.append("accepted high-confidence")
    return reasons

def main():
    proj = project_dir(sys.argv)
    rep = Report("sca_triage")
    fpath = proj / "security" / "findings.json"
    if not fpath.exists():
        print("  ℹ️  no findings.json — treat as no scanner run yet (baseline still requires the scan in CI).")
        rep.print(); return rep.exit_code()
    findings = load_json(fpath).get("findings", [])
    policy = set(load_json(proj / "security" / "policy.json").get("block_on", [])) \
        if (proj / "security" / "policy.json").exists() else {"kev", "exposed_secret", "confirmed", "accepted-high-confidence"}
    triage_open = 0
    for f in findings:
        why = blocks(f, policy)
        if why:
            rep.add(BLOCKED, f.get("id", "?"), f"{f.get('severity','?')} {f.get('cve') or f.get('cwe') or ''} — blocks: {', '.join(why)}")
        elif f.get("status", "untriaged") == "untriaged":
            triage_open += 1
    if triage_open:
        print(f"  ℹ️  {triage_open} untriaged finding(s) opened as TRIAGE tasks (not blocking).")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
