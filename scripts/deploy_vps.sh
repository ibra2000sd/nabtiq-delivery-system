#!/usr/bin/env bash
# deploy_vps.sh — publish a built static site to the Traefik VPS (auto Let's Encrypt SSL).
# The REAL agency deploy path (Rev 2 primitive #6: CI + events, not a skill). Idempotent.
#
# Prereqs (set once — you handle credentials, not this script):
#   VPS_SSH_TARGET        e.g. deploy@45.9.188.149   (an SSH key must already authorize you)
#   SITE_DOMAIN           e.g. test.nabtiq.com
#   TRAEFIK_NETWORK       external docker network Traefik watches   (discover on the VPS once)
#   TRAEFIK_CERTRESOLVER  Traefik ACME resolver name                (discover on the VPS once)
#   PROJECT_DIR           project dir whose build/ to ship (default: projects/demo-fixed)
#
# It does NOT touch any other site on the VPS: it only rsyncs into a per-domain directory
# under /opt/nabtiq-sites/<domain>/ and (re)starts THAT domain's compose project.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-projects/demo-fixed}"
: "${VPS_SSH_TARGET:?set VPS_SSH_TARGET, e.g. deploy@45.9.188.149}"
: "${SITE_DOMAIN:?set SITE_DOMAIN, e.g. test.nabtiq.com}"
: "${TRAEFIK_NETWORK:?set TRAEFIK_NETWORK (discover on the VPS)}"
: "${TRAEFIK_CERTRESOLVER:?set TRAEFIK_CERTRESOLVER (discover on the VPS)}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SITE_SERVICE="$(echo "$SITE_DOMAIN" | tr '.' '-')"
REMOTE_DIR="/opt/nabtiq-sites/${SITE_DOMAIN}"
BUILD="${PROJECT_DIR}/build"

echo "==> building ${PROJECT_DIR}"
python3 scripts/build_site.py "${PROJECT_DIR}"
test -f "${BUILD}/index.html" || { echo "no ${BUILD}/index.html — build failed"; exit 1; }

echo "==> preparing remote ${REMOTE_DIR} on ${VPS_SSH_TARGET}"
ssh "${VPS_SSH_TARGET}" "mkdir -p '${REMOTE_DIR}/site'"

echo "==> rsync site -> VPS (delete stale, never touches other sites)"
rsync -az --delete "${BUILD}/" "${VPS_SSH_TARGET}:${REMOTE_DIR}/site/"

echo "==> render compose for ${SITE_DOMAIN}"
export SITE_SERVICE SITE_DOMAIN TRAEFIK_NETWORK TRAEFIK_CERTRESOLVER
envsubst '${SITE_SERVICE} ${SITE_DOMAIN} ${TRAEFIK_NETWORK} ${TRAEFIK_CERTRESOLVER}' \
  < deploy/traefik-static.compose.yml > /tmp/${SITE_SERVICE}.compose.yml
scp /tmp/${SITE_SERVICE}.compose.yml "${VPS_SSH_TARGET}:${REMOTE_DIR}/docker-compose.yml"

echo "==> (re)deploy the container behind Traefik"
ssh "${VPS_SSH_TARGET}" "cd '${REMOTE_DIR}' && docker compose up -d --remove-orphans"

echo "==> deployed. Traefik will issue/renew the SSL cert for https://${SITE_DOMAIN}"
echo "    verify: curl -I https://${SITE_DOMAIN}"
