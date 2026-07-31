#!/usr/bin/env bash
# first-paint.sh — build a project's page and run the Playwright first-paint probe against it.
# Needs a browser: npm ci && npx playwright install chromium
set -uo pipefail
PROJ="${1:?usage: first-paint.sh <project-dir>}"; shift || true
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
python3 scripts/build_site.py "$PROJ"
PORT="${NABTIQ_PREVIEW_PORT:-8199}"
PID_FILE="$(mktemp)"
( cd "$PROJ/build" && python3 -m http.server "$PORT" >/dev/null 2>&1 & echo $! > "$PID_FILE" )
sleep 1
node probes/first_paint_probe.mjs "http://localhost:$PORT/" "$PROJ/image-manifest.json"; rc=$?
kill "$(cat "$PID_FILE")" 2>/dev/null
rm -f "$PID_FILE"
exit $rc
