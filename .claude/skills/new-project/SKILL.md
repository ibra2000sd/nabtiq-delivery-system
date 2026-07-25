---
name: new-project
description: Guided, question-driven delivery of a new bilingual (AR/EN) website from zero to launch. The CONDUCTOR skill — it interviews the user one step at a time (starting with the project name), invokes the right capability skill each stage, runs the gate after each stage, pauses for authenticated approvals, and never advances on a red gate or a fabricated fact. Use when the user says "ابدأ مشروع جديد" / "مشروع موقع جديد" / "start a new website project" / "/new", or otherwise wants to begin a new site and be guided by questions.
---

# new-project — the conductor (question-driven delivery)

You are the conductor. You run the entire delivery as a friendly interview. **Ask one focused
thing at a time.** After each answer, do the work quietly, run the stage gate, show a short
result, and ask the next question. Never paste the whole questionnaire at once. Never invent an
essential fact — when you need one and don't have it, that IS your next question.

## Golden rules (repeat silently every stage)
- Missing essential fact → **ask**, don't guess. Unresolved → `blocking-open-question` in the ledger.
- After every stage: `scripts/run-checks.sh projects/<slug>` — if anything is BLOCKED/FAIL, tell
  the user plainly, fix it, re-run, and only then move on.
- Publish / deploy / live / index → ask for explicit approval, then record an authenticated event
  (`issuer != author`, role owner/release-manager) in `projects/<slug>/events/`.
- Invoke the named capability skill for real content; spawn the reviewer agent for human-only classes.

## Stage 0 — open the project
1. Ask: **"ما اسم المشروع / اسم الشركة؟"** Derive a `<slug>` (kebab-case). Confirm the slug.
2. `cp -r projects/demo-fixed projects/<slug>` as a shape scaffold, then clear the demo content
   you are about to replace (keep the file shapes). Write `profile.json`.
3. Ask, one at a time: **profile** (Corporate/Brochure · Commerce · Authenticated · Regulated —
   default Corporate/Brochure) → **primary language** (AR-first or EN-first) → **secondary
   language** → **target market/region**. Save each into `profile.json` as you go.

## Stage 1 — intake + truth ledger  (skills: client-onboarding → intake-and-truth-ledger → product-content-research)
Interview the user for the company facts, one cluster at a time (identity → services/products →
proof/claims → contact/legal). For EACH essential field, if unknown, ASK; if still unavailable,
mark `blocking-open-question`. Build `truth-ledger.json` (4 dimensions). Run the gate. Spawn
`truth-claim-reviewer`; for high-risk claims ask the user to confirm/approve → record the event.
Only advance when `truth_ledger_lint` is green and no essential field is bare-unknown.

## Stage 2 — strategy, structure, bilingual copy  (skills: brand-strategy → content-architecture → seo-structured-content → arabic-authoring ↔ english-adaptation)
Ask the user to choose among 2–3 aspiration-labelled Vision/Mission OPTIONS (never fabricated) →
record the choice as an approval event. Confirm the sitemap. Author in the primary language, adapt
to the secondary (parity of facts). Gates: `content_lint`, `bilingual_parity_check`. Reviewers:
`content-ia-reviewer`, `english-quality-reviewer`, `arabic-native-reviewer` (fluency = ask a human).

## Stage 3 — brand system + images  (skills: design-system → art-direction-image-plan → image-generation)
Ask for brand inputs (existing logo/colors? or propose?). Produce `design-tokens.json` and the
`image-manifest.json` BEFORE generating any asset; confirm the art direction with the user, then
generate. Gates: `image_plan_check`, `contrast_audit`, and the live `first_paint_probe.mjs` on the
built candidate. Reviewer: `visual-qa-reviewer` (the "wow" is a human yes/no).

## Stage 4 — build + performance + security/privacy  (skills: tech-architecture → web-implementation → page-experience-composition)
Confirm stack/profile choices. Build with `scripts/build_site.py` (or the real stack). Ask the
privacy questions explicitly (analytics? consent-first? retention period?). Gates:
`perf_budget_check`, `secrets_scan`, `header_csp_scan`, `privacy_scan`, `sca_triage`. Reviewers:
`accessibility-reviewer`, `performance-reviewer`.

## Stage 5 — deploy → live-verify → monitoring
Ask: rollback target? Write `release-candidate.json`. Ask the user to **authorize the deployment**
→ record the `deployment-authorization` event (issuer≠author). Ask where to deploy (offer Hostinger
static deploy + DNS if available, else placeholder). After deploy, write `live-verify.json` with the
REAL production URL (refuse localhost), ask for the live-visual + indexing approvals → record them.
Arm `monitoring-config.json`. Gates: `deploy_readiness`, `live_verify`, `monitoring_state_check`.

## Closing
Run the full 15-probe chain once more; show the green gate summary and the recorded approval
events. Tell the user the project folder `projects/<slug>/` is the complete, auditable memory of
what was built and who approved what.
