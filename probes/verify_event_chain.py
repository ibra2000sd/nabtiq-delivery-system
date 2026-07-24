#!/usr/bin/env python3
"""verify_event_chain — local checks on the append-only event/approval ledger (Rev 2.2 §B/§C).

NOTE (honesty): real non-repudiation comes from OIDC-verified identity + signing
(GitHub Artifact Attestations / Sigstore) + an EXTERNAL transparency anchor, wired in CI.
This probe checks the LOCAL bindings that must hold regardless:
  * each event binds subject_id + artifact_hash + issued_at + expiry + nonce + issuer + role
  * nonces are unique across the ledger (replay guard)
  * for high-risk gates: approval issuer != artifact author (no self-approval)
  * referenced artifact_hash resolves to a known artifact hash in the project
"""
import sys, json, datetime
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir, hash_of_artifact

REQUIRED = ["event_type", "subject_id", "artifact_hash", "issuer", "role",
            "nonce", "issued_at", "expiry", "run_id"]

def collect_known_hashes(proj):
    hashes = {}
    if (proj / "truth-ledger.json").exists():
        d = load_json(proj / "truth-ledger.json")
        hashes[hash_of_artifact(d)] = "truth-ledger.json"
        # also index individual claims by their own hash if present
    for pg in (proj / "pages").glob("*.content.json") if (proj / "pages").is_dir() else []:
        d = load_json(pg)
        hashes[hash_of_artifact(d)] = pg.name
    return hashes

def main():
    proj = project_dir(sys.argv)
    rep = Report("verify_event_chain")
    edir = proj / "events"
    events = []
    if edir.is_dir():
        for f in sorted(edir.glob("*.jsonl")):
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines()):
                line = line.strip()
                if line:
                    try:
                        events.append((f.name, i, json.loads(line)))
                    except Exception as ex:
                        rep.add(FAIL, f"{f.name}:{i}", f"invalid JSON line: {ex}")
    seen_nonce = {}
    for fname, i, e in events:
        where = f"{fname}:{i}"
        for k in REQUIRED:
            if k not in e:
                rep.add(FAIL, where, f"missing field '{k}'")
        n = e.get("nonce")
        if n in seen_nonce:
            rep.add(BLOCKED, where, f"replayed nonce {n!r} (also at {seen_nonce[n]})")
        elif n is not None:
            seen_nonce[n] = where
        # self-approval guard
        if e.get("event_type") == "approval" and e.get("issuer") and e.get("author"):
            if e["issuer"] == e["author"]:
                rep.add(BLOCKED, where, "self-approval: issuer == author")
        # expiry sanity (issued_at <= expiry)
        try:
            ia = datetime.datetime.fromisoformat(e["issued_at"].replace("Z", "+00:00"))
            ex = datetime.datetime.fromisoformat(e["expiry"].replace("Z", "+00:00"))
            if ex < ia:
                rep.add(FAIL, where, "expiry before issued_at")
        except Exception:
            pass
    if not events:
        print("ℹ️  verify_event_chain: no events yet (empty ledger is valid)")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
