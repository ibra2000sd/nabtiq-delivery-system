# Architecture (summary)

Six primitives (see the Revision 2 / 2.1 / 2.2 documents for the full design):

1. **Runtime / state engine** — Git + append-only event ledger + derived index (this repo's `projects/`, `probes/build_project_index.py`).
2. **Capability skills** — stateless instruction packs that each produce one artifact family (`.claude/skills/`).
3. **Fresh-context reviewer agents** — isolated subagents + rubric (`.claude/agents/`).
4. **Validation/evidence probes** — deterministic / controlled-hybrid checks (`probes/`), run in CI.
5. **Scheduled automations** — monitoring/observability (not in this Wave-0 slice; added in Wave 5).
6. **Authenticated human-approval events** — recorded in `events/`, bound + anchored in CI.

Wave 0 ships #1, one example of #2 and #3, four probes of #4, and the #6 event format. Wave 1 adds four baseline security/privacy probes (secrets, headers/CSP, privacy/PDPL wiring, SCA triage),
with a live demo that BLOCKS a bad project and PASSES a remediated one.
