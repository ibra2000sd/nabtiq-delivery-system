#!/usr/bin/env bash
# run-checks.sh — run all validation/evidence probes against a project dir.
# Usage: scripts/run-checks.sh projects/<name>
set -uo pipefail
PROJ="${1:?usage: run-checks.sh <project-dir>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=============================================="
echo " Nabtiq gates  ·  project: $PROJ"
echo "=============================================="
python3 probes/build_project_index.py "$PROJ" >/dev/null

rc=0
for probe in manifest_schema_validate truth_ledger_lint content_lint bilingual_parity_check image_plan_check contrast_audit perf_budget_check secrets_scan header_csp_scan privacy_scan sca_triage verify_event_chain; do
  echo "----------------------------------------------"
  python3 "probes/${probe}.py" "$PROJ" || rc=1
done

echo "=============================================="
if [ "$rc" -eq 0 ]; then
  echo "✅ GATE RESULT: PASS — project may advance."
else
  echo "⛔ GATE RESULT: BLOCKED/FAIL — merge/publish refused. Fix the findings above."
fi
echo "=============================================="
exit "$rc"
