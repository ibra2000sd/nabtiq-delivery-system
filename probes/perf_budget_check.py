#!/usr/bin/env python3
"""perf_budget_check — Core Web Vitals + weight budgets (Rev 2.2 §F; class: HYBRID).

Reads <proj>/perf-report.json: per-route measured lab values + budgets. Blocks when a measured
value EXCEEDS its human-set budget. The budget is a human decision, and lab != field — a green
lab result is evidence, not a guarantee of real-user (field) performance.
Route shape: { path, lcp_ms, budget_lcp_ms, inp_ms, budget_inp_ms, cls, budget_cls, total_kb, budget_kb }
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, load_json, project_dir

CHECKS = [("lcp_ms", "budget_lcp_ms", "LCP ms"), ("inp_ms", "budget_inp_ms", "INP ms"),
          ("cls", "budget_cls", "CLS"), ("total_kb", "budget_kb", "weight KB")]

def main():
    proj = project_dir(sys.argv)
    rep = Report("perf_budget_check")
    path = proj / "perf-report.json"
    if not path.exists():
        print("  ℹ️  no perf-report.json — lab CWV not measured yet (run against the candidate build in CI).")
        rep.print(); return rep.exit_code()
    for route in load_json(path).get("routes", []):
        rp = route.get("path", "?")
        for meas_k, budg_k, label in CHECKS:
            meas, budg = route.get(meas_k), route.get(budg_k)
            if meas is not None and budg is not None and meas > budg:
                rep.add(BLOCKED, f"{rp}", f"{label} {meas} exceeds budget {budg}")
    print("  ℹ️  class=HYBRID: lab measurement vs a human-set budget; field (real-user) CWV still monitored post-launch.")
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
