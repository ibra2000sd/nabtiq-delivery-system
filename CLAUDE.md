# Nabtiq Delivery System — session guide (auto-loaded by Claude Code)

This repository IS the operating system for delivering premium bilingual (AR/EN) websites.
It carries capability **skills** (`.claude/skills/`), fresh-context **reviewer agents**
(`.claude/agents/`), deterministic **probes** (`probes/`), CI **gates/automations**
(`.github/workflows/`), and an append-only **event ledger** (per project `events/`).

## Guided Delivery Mode (question-driven)

When the user says any of: **"ابدأ مشروع جديد" / "مشروع موقع جديد" / "start a new website
project" / `/new`**, enter **Guided Delivery Mode** and follow the **`new-project`** skill.
In this mode YOU drive the whole delivery as an interview: you ask, the user answers, you do
the work, you run the gate, you show the result, and you only advance when it is green and the
required approval is recorded. Ask **one focused thing at a time**, starting with the project
name. Never dump the whole questionnaire at once.

When the user supplies a real client package or asks to replace an existing website, use the broader
**`studio-delivery`** conductor. It adds source inventory, current-site migration, creative direction,
motion direction, still/video production, independent review, and the same release controls.

## Invariants that hold in EVERY session (never bypass, even in a hurry)

1. **Never invent an essential fact — ASK.** Company name, founding year, license/CR number,
   contact details, service specifics, prices: if it is missing, ask the user; if still
   unavailable, record it as `blocking-open-question` in the truth ledger. Never write a
   plausible guess. (The blind forward-test proved a plausible-but-false claim is exactly what
   the automated gate will NOT catch.)
2. **Parity of FACTS, not words**, across Arabic and English. Numbers, dates, names must match.
3. **Gates are the hard enforcement.** After each build stage run
   `scripts/run-checks.sh projects/<slug> build`
   and DO NOT advance the interview while any probe is BLOCKED/FAIL. Fix, re-run, then continue.
4. **High-risk publish, deploy, live-verify, and indexing require an AUTHENTICATED approval
   event** (`events/*.jsonl`, `issuer != author`, role owner/release-manager). Ask the user to
   approve explicitly, then record the event. No self-approval.
5. **Skills don't self-run and reviewers don't self-approve.** You invoke a capability skill to
   produce an artifact, then spawn the matching reviewer agent; a human resolves the human-only
   classes (Arabic fluency, factual truth, visual "wow").
6. **Deploy target:** the `nabtiq-deploy` workflow's deploy step is a placeholder — a real host
   (e.g. Hostinger static deploy + DNS) is wired only when the user asks.

## Where state lives
`projects/<slug>/` is the whole project memory: `profile.json`, `brand.json`,
`site-map.json`, `truth-ledger.json`, `pages/*.content.json`, `image-manifest.json`,
`video-manifest.json`, `site-strategy.json`, `creative-direction.json`, `motion-spec.json`,
`generation-plan.json`, `design-tokens.json`, `security/*`,
`perf-report.json`, `release-candidate.json`, `live-verify.json`, `monitoring-config.json`,
and `events/*.jsonl` (the audit trail). For the implemented Corporate/Brochure Alpha,
create a project with `scripts/new_project.py`; do not copy a legacy demo.

## External media execution

`scripts/media_pipeline.py` defaults to dry-run. `--execute` is an explicit authorization boundary:
it may create paid provider jobs. Image generation reads `OPENAI_API_KEY`; video generation reads
`LUMA_AGENTS_API_KEY`. Values belong only in the operator environment and must never be written to
project artifacts, prompts, logs, commits, or delivery archives.
