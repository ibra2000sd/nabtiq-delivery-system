#!/usr/bin/env bash
# Run validation/evidence probes for a project.
# Usage: scripts/run-checks.sh projects/<name> [build|release]
set -uo pipefail
PROJ="${1:?usage: run-checks.sh <project-dir> [build|release]}"
STAGE="${2:-build}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$STAGE" != "build" && "$STAGE" != "release" ]]; then
  echo "invalid stage: $STAGE (expected build|release)" >&2
  exit 2
fi

echo "=============================================="
echo " Nabtiq gates  ·  project: $PROJ · stage: $STAGE"
echo "=============================================="
python3 probes/build_project_index.py "$PROJ" >/dev/null

rc=0
base_probes=(
  manifest_schema_validate
  truth_ledger_lint
  content_lint
  bilingual_parity_check
  image_plan_check
  contrast_audit
  perf_budget_check
  secrets_scan
  header_csp_scan
  privacy_scan
  sca_triage
)

alpha_probes=()
if [[ -f "$PROJ/site-map.json" ]]; then
  alpha_probes=(
    site_contract_check
    studio_contract_check
    asset_integrity_check
    video_asset_check
    build_output_check
    seo_output_check
  )
fi

release_probes=()
if [[ "$STAGE" == "release" ]]; then
  release_probes=(deploy_readiness live_verify monitoring_state_check verify_event_chain)
  for required in release-candidate.json live-verify.json monitoring-config.json; do
    if [[ ! -f "$PROJ/$required" ]]; then
      echo "⛔ [BLOCKED] release stage requires $PROJ/$required"
      rc=1
    fi
  done
fi

for probe in "${base_probes[@]}" ${alpha_probes[@]+"${alpha_probes[@]}"} ${release_probes[@]+"${release_probes[@]}"}; do
  echo "----------------------------------------------"
  python3 "probes/${probe}.py" "$PROJ" || rc=1
done

echo "=============================================="
if [[ "$rc" -eq 0 ]]; then
  echo "✅ GATE RESULT: PASS — $STAGE stage may advance."
else
  echo "⛔ GATE RESULT: BLOCKED/FAIL — $STAGE stage refused."
fi
echo "=============================================="
exit "$rc"
