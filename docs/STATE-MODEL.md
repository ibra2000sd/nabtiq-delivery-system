# State model (the project's "second brain")

Canonical authority: **Git** (artifact bytes + history) + an **append-only event ledger**
(`projects/<p>/events/*.jsonl`). The **project index** (`index.json`) is a DERIVED read-model,
rebuildable at any time from Git + events — never the source of truth.

- **Facts memory** → `truth-ledger.json` (4-dimension claims).
- **Decision memory** → `events/*.jsonl` (gate verdicts + approvals; cryptographically bound and
  externally anchored in CI so deletion/history-rewrite is *detectable* — see Revision 2.2 §B).
- **Fast recall** → `index.json` (what the delivery-router reads first; it does NOT load every artifact).

Threat model: a malicious repo admin is IN SCOPE — an in-repo ledger is *not* inherently immutable,
which is why events are signed and anchored to an external transparency log in CI. This local repo
demonstrates the bindings; the crypto/OIDC/anchor layer is wired in `.github/workflows` at execution.
