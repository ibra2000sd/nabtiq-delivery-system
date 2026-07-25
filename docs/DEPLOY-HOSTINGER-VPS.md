# Deploy — Hostinger Docker + Traefik VPS (the real agency path)

The `nabtiq-deploy` workflow's deploy step is now a REAL deploy to the Traefik VPS, not a
placeholder. Static sites are published as per-domain `nginx:alpine` containers behind the VPS's
existing Traefik, which issues and renews Let's Encrypt SSL automatically per host.

## Target (this account) — verified on the live box
- VPS: `srv1731411.hstgr.cloud` · **45.9.188.149** · Ubuntu 24.04 + Docker + Traefik · paid to 2028.
- `nabtiq.com` already resolves here (DNS `@` ALIAS → `srv1731411.hstgr.cloud`) and ~10 live client
  sites run on it (goldentur, kaltomb, ilariae, nabfx, …). The VPS is LIVE. **Never clobber it** —
  deploys only write under `/opt/nabtiq-sites/<domain>/` and manage that domain's own compose project.
- Test subdomain `test.nabtiq.com` → A `45.9.188.149` (added; other records untouched).

## This VPS's Traefik pattern (important — differs from the generic template)
Traefik runs in **host network mode** and reaches each site over that site's OWN per-compose bridge
network. There is **no shared external Traefik network**, and site containers carry **no
`traefik.docker.network` label** (each is on exactly one network). Traefik does a **global
HTTP→HTTPS redirect** at the entrypoint, so no per-site redirect labels are needed. ACME resolver
is **`letsencrypt`** (HTTP-01 on the `web` entrypoint). `deploy/traefik-static.compose.yml` already
matches this pattern — the only value to supply is `TRAEFIK_CERTRESOLVER=letsencrypt`.

## Enable CI deploy (you set the credentials — the system never handles them)
In the GitHub repo settings add:
- secret `VPS_SSH_KEY` — the private deploy key whose public half is in the VPS's `authorized_keys`
  (on this account: the `nabtiq_vps_deploy` key used by the `nabtiq-vps` SSH host alias).
- secret `VPS_SSH_TARGET` — `root@45.9.188.149`.
- secret `VPS_KNOWN_HOSTS` — output of `ssh-keyscan 45.9.188.149`.
- variable `TRAEFIK_CERTRESOLVER` — `letsencrypt`.

Then run **Actions → nabtiq-deploy** (workflow_dispatch) with `project` and `domain`. The job:
1. re-runs the full 15-probe chain + `deploy_readiness` (authenticated deployment-authorization event),
2. rsyncs `projects/<project>/build/` to `/opt/nabtiq-sites/<domain>/site/` (with `--delete`, that
   domain only),
3. renders `deploy/traefik-static.compose.yml` and `docker compose up -d`,
4. runs `live_verify` + `monitoring_state_check` against the project.
If `VPS_SSH_KEY` is unset the deploy is skipped (gates still enforced) so forks never fail.

## Manual / first deploy
`scripts/deploy_vps.sh` does the same locally: set `VPS_SSH_TARGET`, `SITE_DOMAIN`,
`TRAEFIK_NETWORK`, `TRAEFIK_CERTRESOLVER`, `PROJECT_DIR`, then run it. It builds, rsyncs into the
per-domain dir, and (re)starts only that domain's container.

## Rollback
`release-candidate.json.rollback_target` records the previous release. Because each domain is its
own compose project + versioned `site/` dir, rollback = re-deploy the previous build (or keep a
`site.prev/` and swap). Never a partial in-place edit.
