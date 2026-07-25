#!/usr/bin/env python3
"""monitoring_state_check — G22: monitoring must be ARMED, not assumed (Rev 2.1 §J.2 step 9).
Stage-aware: skips if there is no monitoring-config.json.

Monitoring is a SCHEDULED AUTOMATION + observability, never a 'skill that runs continuously'
(Rev 2 primitive #5). This probe only confirms the automations are configured and armed:
uptime, RUM (field CWV), error tracking, dependency-vuln watch (re-triggers sca_triage on new KEV),
and a content-freshness cadence. A silent monitor reads as healthy — so we require proof it reports.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, load_json, project_dir

REQUIRED = ["uptime", "rum", "error_tracking", "dep_vuln_watch"]

def main():
    proj = project_dir(sys.argv)
    rep = Report("monitoring_state_check")
    path = proj / "monitoring-config.json"
    if not path.exists():
        print("  ℹ️  no monitoring-config.json — not at monitoring stage (skip).")
        rep.print(); return rep.exit_code()
    d = load_json(path)
    for k in REQUIRED:
        if d.get(k) is not True:
            rep.add(BLOCKED, "monitoring", f"'{k}' automation not armed (must be true)")
    if not d.get("content_freshness"):
        rep.add(BLOCKED, "monitoring", "no content_freshness cadence set")
    print("  ℹ️  monitoring = scheduled automations + observability (.github/workflows/monitoring.yml), not a skill.")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
