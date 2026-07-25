#!/usr/bin/env python3
"""deploy_readiness — a project cannot deploy without rollback readiness + an AUTHENTICATED
deployment-authorization event (Rev 2.1 §J.2 step 7). Stage-aware: skips if there is no
release-candidate.json (the project hasn't reached release).

Blocks when a release-candidate exists but:
  * rollback_target is missing/null (no atomic-rollback readiness)
  * gates_green is not true (blocking gates still open)
  * there is no deployment-authorization approval event for this release with issuer != author
"""
import sys, json
from pathlib import Path
from lib_common import Report, BLOCKED, load_json, project_dir

def deploy_authorized(proj, subject_id):
    edir = proj / "events"
    if not edir.is_dir():
        return False
    for f in edir.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            if (e.get("event_type") == "approval" and e.get("subject_id") == subject_id
                    and e.get("decision") == "approved" and e.get("role") in ("owner", "release-manager")
                    and e.get("issuer") and e.get("author") and e["issuer"] != e["author"]):
                return True
    return False

def main():
    proj = project_dir(sys.argv)
    rep = Report("deploy_readiness")
    path = proj / "release-candidate.json"
    if not path.exists():
        print("  ℹ️  no release-candidate.json — project not at release stage (skip).")
        rep.print(); return rep.exit_code()
    rc = load_json(path)
    if not rc.get("rollback_target"):
        rep.add(BLOCKED, "release", "no rollback_target — refuse deploy without atomic-rollback readiness")
    if rc.get("gates_green") is not True:
        rep.add(BLOCKED, "release", "gates_green is not true — blocking gates still open")
    subj = rc.get("id") or f"release:{proj.name}"
    if not deploy_authorized(proj, subj):
        rep.add(BLOCKED, "release", f"no authenticated deployment-authorization event (issuer≠author) for {subj}")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
