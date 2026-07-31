#!/usr/bin/env bash
# One-command reproducible verification for the Functional Internal Alpha.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PROJECT="${1:-projects/alpha-corporate}"

python3 scripts/build_site.py "$PROJECT"
bash scripts/run-checks.sh "$PROJECT" build
python3 -m unittest discover -s tests -p 'test_*.py' -v
