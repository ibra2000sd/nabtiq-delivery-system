#!/usr/bin/env python3
"""truth_ledger_lint — enforces the 4-dimension truth model (Rev 2.2 §D).

Dimensions per claim:
  evidence_status     : verified | owner-attested | unverified | unknown
  claim_risk          : low | medium | high | regulated
  publication_mode    : as-fact | attributed | aspirational | marketing | omitted | blocked
  required_approver_role : owner | legal | privacy | tax | finance | food-safety | certification

Core rules (a passing ledger cannot publish an unsupported/unapproved claim):
  * publishable + publication_mode==as-fact     -> requires evidence_status==verified
  * publishable + publication_mode==attributed  -> requires evidence_status in {verified, owner-attested}
  * publishable + publication_mode==aspirational -> requires an owner approval EVENT bound to the claim
  * publishable + publication_mode==marketing   -> requires an owner approval EVENT; must carry no factual assertion
  * evidence_status in {unverified} published as fact/attributed -> BLOCKED (blocked-unverified, unblockable with evidence)
  * evidence_status==unknown published in any mode -> BLOCKED (route to a client question)
  * policy_prohibited==true -> BLOCKED always (Nabtiq-adopted ban)
  * claim_risk in {high, regulated} published as-fact -> ALSO requires an approval event of the required domain role
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir

EVIDENCE = {"verified", "owner-attested", "unverified", "unknown"}
RISK = {"low", "medium", "high", "regulated"}
MODE = {"as-fact", "attributed", "aspirational", "marketing", "omitted", "blocked"}
ROLES = {"owner", "legal", "privacy", "tax", "finance", "food-safety", "certification"}

def load_events(proj):
    events = []
    edir = proj / "events"
    if edir.is_dir():
        for f in sorted(edir.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    events.append(__import__("json").loads(line))
    return events

def has_approval(events, claim_id, roles):
    for e in events:
        if (e.get("event_type") == "approval"
                and e.get("subject_id") == claim_id
                and e.get("role") in roles
                and e.get("decision") == "approved"):
            return True
    return False

def main():
    proj = project_dir(sys.argv)
    rep = Report("truth_ledger_lint")
    ledger_path = proj / "truth-ledger.json"
    if not ledger_path.exists():
        rep.add(BLOCKED, "truth-ledger.json", "missing truth ledger")
        rep.print(); return rep.exit_code()
    ledger = load_json(ledger_path)
    events = load_events(proj)

    for c in ledger.get("claims", []):
        cid = c.get("id", "?")
        ev, risk, mode = c.get("evidence_status"), c.get("claim_risk"), c.get("publication_mode")
        role = c.get("required_approver_role")
        publishable = bool(c.get("publishable", False))

        # enum integrity
        for name, val, allowed in [("evidence_status", ev, EVIDENCE), ("claim_risk", risk, RISK),
                                    ("publication_mode", mode, MODE), ("required_approver_role", role, ROLES)]:
            if val not in allowed:
                rep.add(FAIL, cid, f"invalid {name}={val!r}")

        if c.get("policy_prohibited"):
            if publishable:
                rep.add(BLOCKED, cid, "policy-prohibited claim marked publishable")
            continue

        if not publishable:
            continue  # not published -> nothing to enforce for publication

        # the core blocking rules
        if ev == "unknown":
            rep.add(BLOCKED, cid, "unknown claim cannot be published — route to a client question")
        elif mode == "as-fact":
            if ev != "verified":
                rep.add(BLOCKED, cid,
                        f"as-fact requires evidence_status=verified, got {ev} (blocked-unverified: unblock with evidence)")
            elif risk in ("high", "regulated") and not has_approval(events, cid, {role, "legal"}):
                rep.add(BLOCKED, cid,
                        f"{risk} claim as-fact needs an approval event of role '{role}' (or legal); none found")
        elif mode == "attributed":
            if ev not in ("verified", "owner-attested"):
                rep.add(BLOCKED, cid, f"attributed requires verified/owner-attested, got {ev}")
        elif mode == "aspirational":
            if not has_approval(events, cid, {"owner"}):
                rep.add(BLOCKED, cid, "aspirational claim needs an owner approval event; none found")
        elif mode == "marketing":
            if not has_approval(events, cid, {"owner"}):
                rep.add(BLOCKED, cid, "marketing claim needs an owner approval event; none found")

    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
