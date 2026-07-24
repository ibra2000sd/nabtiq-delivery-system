#!/usr/bin/env python3
"""privacy_scan — PDPL/privacy WIRING (Rev 2.2 §item 12; class: HYBRID).

Proves the *wiring* is present (consent gate, retention, notice, declared lawful basis).
It does NOT prove legal PDPL/GDPR compliance — that is a qualified legal/privacy judgement.
Consent-first analytics is Nabtiq's conservative DEFAULT policy, not the only lawful basis;
the lawful basis is a project/jurisdiction legal decision. Regulated profiles need a legal
approval event + DPIA. Baseline is MANDATORY: missing artifact BLOCKS.
Reads <proj>/security/privacy.json  (+ <proj>/profile.json for the profile).
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

LAWFUL = {"consent", "legitimate-interest", "contract", "legal-obligation", "vital-interest", "public-task"}

def has_legal_approval(proj):
    edir = proj / "events"
    if not edir.is_dir():
        return False
    import json
    for f in edir.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                if e.get("event_type") == "approval" and e.get("role") in ("legal", "privacy") and e.get("decision") == "approved":
                    return True
    return False

def main():
    proj = project_dir(sys.argv)
    rep = Report("privacy_scan")
    profile = (load_json(proj / "profile.json") if (proj / "profile.json").exists() else {}).get("profile")
    path = proj / "security" / "privacy.json"
    if not path.exists():
        rep.add(BLOCKED, "security/privacy.json",
                "missing — baseline privacy wiring is MANDATORY (notice, lawful basis, retention, consent)")
        rep.print(); return rep.exit_code()
    d = load_json(path)

    if not d.get("privacy_notice_url"):
        rep.add(BLOCKED, "privacy", "no privacy_notice_url")
    lb = d.get("lawful_basis")
    if lb not in LAWFUL:
        rep.add(BLOCKED, "privacy", f"lawful_basis unset/invalid ({lb!r}) — must be a declared legal decision")
    if not d.get("retention_days"):
        rep.add(BLOCKED, "privacy", "no retention period set for collected data")

    analytics = d.get("analytics_enabled")
    essential = d.get("analytics_essential", False)
    if analytics and not essential:
        # consent-first is Nabtiq's default; if lawful_basis is consent, the gate must be wired
        if lb == "consent" and not d.get("consent_before_analytics"):
            rep.add(BLOCKED, "privacy",
                    "non-essential analytics under a 'consent' basis but consent_before_analytics is false "
                    "(Nabtiq default policy = consent-first; wire the gate or record a different lawful basis with legal approval)")

    if profile == "regulated":
        if not d.get("dpia_ref"):
            rep.add(BLOCKED, "privacy", "regulated profile requires a DPIA reference (dpia_ref)")
        if not has_legal_approval(proj):
            rep.add(BLOCKED, "privacy", "regulated profile requires a legal/privacy approval event")

    print("  ℹ️  class=HYBRID: wiring verified — NOT a proof of legal PDPL/GDPR compliance (qualified human judgement required).")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
