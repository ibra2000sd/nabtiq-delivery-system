# End-to-end test — prove the gates + attestation run on a real PR

Goal: confirm the whole loop works live before adding more capability waves.
Prereqs: a GitHub account + `git` (and optionally the `gh` CLI).

## 0. Use the canonical repo
```bash
cd ~/Golden-ish/nabtiq-delivery-system
```

## 1. Create the GitHub repo & push
```bash
git init -b main 2>/dev/null; git add -A && git commit -m "Nabtiq delivery system" 2>/dev/null
# with gh CLI:
gh repo create nabtiq-delivery-system --public --source=. --push
# or manually: create an empty repo on github.com, then:
#   git remote add origin https://github.com/<you>/nabtiq-delivery-system.git
#   git push -u origin main
```
> Use **--public** so GitHub Artifact Attestations work on a Free/Pro/Team plan.
> Private/internal repos require **GitHub Enterprise Cloud** (verified limitation).

## 2. Watch the gates run (Actions tab → "nabtiq-gates")
Expected on the initial push:
- **gates** job → GREEN: `demo-fixed` passes all 9 probes; the self-test confirms `demo-goldenish` is BLOCKED.
- **attest-gate-evidence** job → GREEN: produces a Sigstore-signed build-provenance attestation of
  `projects/demo-fixed/index.json`, recorded in the Rekor transparency log.

Verify the signed attestation locally:
```bash
gh attestation verify projects/demo-fixed/index.json -R <you>/nabtiq-delivery-system
```

## 3. Prove the gate BLOCKS a bad PR (the real test)
```bash
git checkout -b break-it
echo "AWS_SECRET_ACCESS_KEY=AKIA0000000000000000" > projects/demo-fixed/security/oops.env
git add -A && git commit -m "test: introduce a leaked secret"
git push -u origin break-it
gh pr create --fill      # or open the PR on github.com
```
Expected: **nabtiq-gates FAILS on the PR** (`secrets_scan` blocks the leaked key) → the PR shows a red check.
Clean up:
```bash
git checkout main && git branch -D break-it
# delete the remote branch / close the PR too
```

## 4. Turn the red check into a real merge block (branch protection)
Repo **Settings → Branches → Add rule** for `main` → **Require status checks to pass** → select **nabtiq-gates**.
Now a failing gate actually prevents merge — this is where CI becomes the hard enforcement layer.

## 5. (Optional) enable the Claude reviewer on PRs
1. Install the Claude GitHub App: run `/install-github-app` in Claude Code, or https://github.com/apps/claude
2. Add repo **secret** `ANTHROPIC_API_KEY`.
3. Add repo **variable** `ENABLE_CLAUDE_REVIEW = true`.
`claude-review.yml` will then run the `truth-claim-reviewer` and `content-ia-reviewer` subagents on each PR.

## Honest notes
- Attestations need a public repo (Free/Pro/Team) or Enterprise Cloud.
- Pin `actions/attest-build-provenance` to the current major version (confirm on GitHub docs).
- The gate self-test is intentional: CI **passes** when `demo-goldenish` is correctly blocked.
