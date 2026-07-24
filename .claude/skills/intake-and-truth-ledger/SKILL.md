---
name: intake-and-truth-ledger
description: Capability skill. Ingests client materials and produces the project truth ledger — every claim classified on four orthogonal dimensions (evidence_status, claim_risk, publication_mode, required_approver_role) — plus a list of focused open questions for gaps. Never invents facts. Use at project intake, or when the user says "extract the facts / build the truth ledger / onboard this client".
---
# intake-and-truth-ledger

You turn raw client materials into a **truth ledger** (`truth-ledger.json`). You are a *capability* skill:
stateless, you read materials and write ONE artifact family. You do not approve your own work — a
separate `truth-claim-reviewer` agent and the `truth_ledger_lint` probe judge it.

## Rules
1. **Never invent** a fact, certification, statistic, origin, tax status, or guarantee.
2. Classify every claim on all four dimensions:
   - `evidence_status`: verified | owner-attested | unverified | unknown
   - `claim_risk`: low | medium | high | regulated
   - `publication_mode`: as-fact | attributed | aspirational | marketing | omitted | blocked
   - `required_approver_role`: owner | legal | privacy | tax | finance | food-safety | certification
3. A superlative ("leading/largest/best") without evidence → `evidence_status: unverified` and it will be
   **blocked-unverified** (not banned) until evidence is supplied. Do NOT mark it publishable-as-fact.
4. Anything you cannot ground → `unknown`, and add a focused question to `open-questions`. Do not fill gaps.
5. Emit `truth-ledger.json` using the envelope (id, type, schema_version, project, content_hash) and then
   run `python3 scripts/seal.py <path>` to set the content hash.

## Definition of done
`python3 probes/truth_ledger_lint.py <project-dir>` returns PASS **only after** the owner has supplied
evidence/approvals; until then BLOCKED findings are expected and correct — surface them, don't hide them.
