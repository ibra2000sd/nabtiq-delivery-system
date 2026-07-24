#!/usr/bin/env bash
# first-paint.sh — build a project's page and run the Playwright first-paint probe against it.
# Needs a browser: npm i playwright && npx playwright install chromium   (cloud/CI have it prewired)
set -uo pipefail
PROJ="${1:?usage: first-paint.sh <project-dir> [--flaw svg-flash]}"; shift || true
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
python3 scripts/build_site.py "$PROJ" "$@"
PORT=8199
( cd "$PROJ/build" && python3 -m http.server "$PORT" >/dev/null 2>&1 & echo $! > /tmp/np.pid )
sleep 1
node probes/first_paint_probe.mjs "http://localhost:$PORT/" "$PROJ/image-manifest.json"; rc=$?
kill "$(cat /tmp/np.pid)" 2>/dev/null
exit $rc
