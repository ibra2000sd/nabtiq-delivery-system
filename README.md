# Nabtiq Website-Delivery System — Wave 0 (foundation + live demo)

This is the **first buildable slice** of the Nabtiq system: the runtime/state layer, the core
contracts, four runnable validation probes, one capability skill + two fresh-context reviewer
agents for **Claude Code**, a CI gate — and a **live demo that catches a real error**.

It deliberately does **not** implement all 15 candidate skills. Per the architecture (Revisions
2 / 2.1 / 2.2), we build the foundation + a vertical slice first, forward-test it, then expand.
The skill count remains **provisional**.

## Try it in 10 seconds

```bash
make demo
# or:
bash scripts/run-checks.sh projects/demo-goldenish   # -> BLOCKED (exit 1)
bash scripts/run-checks.sh projects/demo-fixed       # -> PASS    (exit 0)
```

`demo-goldenish` is a Golden-Tur-style project seeded with real failures. The gates catch:
- an **unsupported superlative** ("the leading sesame exporter") → *blocked-unverified*;
- an **aspiration published without an owner approval event**;
- a product page with an **unresolved essential field** (`documented_origin` = blocking-open-question)
  and one left `unknown` → publication blocked (you cannot pass a thin page by filling fields with "unknown").

`demo-fixed` is the remediated version (superlative replaced with a verified statement, aspiration
approved via an event, essential fields resolved) → it PASSES.

## What's inside

| Path | Primitive | What |
| --- | --- | --- |
| `projects/<p>/truth-ledger.json` | state | facts memory — 4-dimension claims |
| `projects/<p>/events/*.jsonl` | state | decision memory — append-only, bound + anchored in CI |
| `projects/<p>/index.json` | state | derived read-model the router reads first |
| `probes/*.py` | probes | truth-lint, content-lint, manifest/hash, event-chain (zero deps) |
| `.claude/agents/*.md` | reviewers | fresh-context subagents + rubric |
| `.claude/skills/*/SKILL.md` | skills | capability instruction pack |
| `.claude/settings.json` | hooks | run a probe on edit (verify hook schema vs current Claude Code docs) |
| `.github/workflows/gates.yml` | CI | gates + a self-test that the blocker *actually blocks* |
| `schemas/*.json` | contracts | JSON Schemas for the artifacts |

## The four dimensions of truth (per claim)
`evidence_status` (verified / owner-attested / unverified / unknown) ·
`claim_risk` (low / medium / high / regulated) ·
`publication_mode` (as-fact / attributed / aspirational / marketing / omitted / blocked) ·
`required_approver_role` (owner / legal / privacy / tax / finance / food-safety / certification).
A **verified** claim can still be **high-risk** and need a domain approver. Unsupported superlatives
are **blocked-unverified** (unblock with evidence), not permanently banned unless Nabtiq adopts a policy.

## Honesty notes
- Real non-repudiation (OIDC identity, GitHub Artifact Attestations / Sigstore, external transparency
  anchor) is wired in **CI**, not in the local probes; a malicious repo admin is in the threat model.
- The probes are pragmatic (stdlib) enforcement of the contract rules, not a full JSON-Schema engine.
- Exact Claude Code hook/agent frontmatter keys evolve — confirm against current docs before relying on them.

## Next waves
Wave 1 baseline security/privacy probes · Wave 2 content chain skills + reviewers ·
Wave 3 visual/first-paint probes · Wave 4 build/a11y/perf · Wave 5 deploy/live-verify/monitoring.
Then run the **two-pass blind forward-test** (Revision 2.2 §E) and derive the interim core-chain count.

## Wave 1 — baseline security & privacy (mandatory in every profile)

Four more probes run on every project (added to `scripts/run-checks.sh`), and **baseline security is
mandatory — a missing security artifact BLOCKS**:

| Probe | Class | Blocks on |
| --- | --- | --- |
| `secrets_scan` | deterministic | any exposed secret in the project subtree |
| `header_csp_scan` | hybrid | missing baseline header; flags `unsafe-inline` / no Trusted Types (human confirms CSP strength) |
| `privacy_scan` | hybrid | missing notice / lawful basis / retention; broken consent wiring — proves *wiring*, **not** legal compliance |
| `sca_triage` | hybrid + triage | **only** KEV / exposed-secret / confirmed / accepted-high-confidence — an untriaged "High" opens a triage task, it does **not** auto-block |

The `demo-goldenish` project now also carries a **leaked AWS key**, a **weak CSP** (missing HSTS,
`unsafe-inline`, no Trusted Types), **broken consent wiring** (non-essential analytics with
`consent_before_analytics:false` under a consent basis, no retention), and a **known-exploited (KEV)
dependency** — all blocked. Its untriaged SAST "High" correctly opens a triage task **without** blocking.
`demo-fixed` resolves them (clean secrets, full headers + Trusted Types, consent gated + retention set,
KEV removed) and passes — while still carrying an untriaged "High" that opens triage but does not block.

**PDPL note:** consent-first analytics is Nabtiq's conservative *default policy*, not the only lawful
basis under Saudi PDPL. The lawful basis is a project/jurisdiction legal decision; regulated projects
require a legal/privacy approval event + DPIA. A privacy scan never asserts legal compliance.

## Wave 2 — content chain (skills + reviewers + bilingual parity)

Adds the content capability skills (`.claude/skills/`): `brand-strategy`, `content-architecture`,
`product-content-research`, `arabic-authoring`, `english-adaptation`, `seo-structured-content`; and two
fresh-context reviewer agents (`.claude/agents/`): `english-quality-reviewer`, `content-ia-reviewer`.

New probe `bilingual_parity_check` (deterministic) enforces **parity of FACTS, not literal words**: for a
bilingual product page, EN and AR must reference the SAME `claim_refs`. `demo-goldenish` now seeds a
divergence (EN references `claim:0002`, AR omits it) → BLOCKED. Native Arabic *fluency* is judged by the
`arabic-native` reviewer agent, never by a probe. Bilingual sequencing (Rev 2.1 §E.3): author → language
review → adaptation → parity review → owner approval bound to **both** locale hashes.

## Claude Code integration (verified 2026-07-24)

Formats confirmed against official docs (see `docs/CLAUDE-CODE-INTEGRATION.md`): subagent frontmatter,
Agent-Skills `SKILL.md`, the **corrected hooks** (stdin-JSON, not env vars) via `.claude/hooks/post_edit_check.py`,
`anthropics/claude-code-action@v1`, and **real GitHub Artifact Attestations** of gate evidence in CI
(`actions/attest-build-provenance`, Sigstore + Rekor; public repos on Free/Pro/Team, private needs Enterprise Cloud).

## Wave 3 — visual chain (image plan + first-paint reliability)

Adds visual capability skills (`.claude/skills/`): `art-direction-image-plan`, `page-experience-composition`
(restored per Rev 2.1 item 10), `design-system` (DTCG, supported token types only), `image-generation`; and a
fresh-context `visual-qa-reviewer` agent.

Two-part visual reliability (the honest split of Rev 2.2 §G.2):
- **`image_plan_check` (stdlib, deterministic)** — the static plan/asset half, wired into the gates. Blocks:
  **SVG fallback** (first-paint SVG-before-raster flash risk), a **documentary slot with no source**
  (fake-facility/cert guard), a **missing asset** (IO-missing), missing **Light/Dark** variant, incomplete plan.
- **`probes/first_paint_probe.mjs` (Playwright, controlled hybrid)** — the runtime frame-level half: pins
  browser/viewport/network/cache and runs the condition matrix (AR/EN · light/dark · desktop/mobile · cold/warm
  cache · slow network · no-JS · IO-missing/dead · post-wait), asserting **zero SVG requests** where prohibited.
  It **activates in Wave 4** against a built candidate (needs `npm i playwright`); it is deliberately NOT in the
  zero-dependency CI yet. A probe supplies evidence; the aesthetic "wow" is a human owner decision.

`demo-goldenish` now also seeds an SVG-fallback hero, a missing dark variant, a documentary facility with no
source, and missing image assets → all blocked. `demo-fixed` ships a clean manifest with present assets → passes.

## Wave 4 — build, accessibility, performance (+ LIVE first-paint)

Adds capability skills `tech-architecture` (stack/ADR/profile) and `web-implementation` (semantic HTML,
RTL via CSS logical properties, raster hero with `fetchpriority`, consent-gated analytics) with a tiny
reference renderer `scripts/build_site.py`; and fresh-context `accessibility-reviewer` + `performance-reviewer`.

New stdlib gates (wired in):
- **`contrast_audit`** — WCAG 2.2 AA. Deterministic for solid colours (blocks `#999` on `#fff` = 2.85:1);
  text-over-image/translucent pairs are **flagged HYBRID** for human review, never auto-passed.
- **`perf_budget_check`** — blocks a route whose lab LCP/INP/CLS or weight exceeds its human-set budget
  (lab ≠ field; real-user CWV is monitored post-launch).

**The first-paint probe is now LIVE** (`probes/first_paint_probe.mjs`, Playwright). It runs against a real
built page across the pinned condition matrix and **catches the SVG-before-raster flash**:
```bash
make first-paint                                   # demo-fixed build -> PASS (raster hero, IO-dead handled)
bash scripts/first-paint.sh projects/demo-goldenish --flaw svg-flash   # -> FAIL (SVG request where prohibited)
```
This proves the exact Golden Tur visual failure is caught on a real page, not just in the plan.
