# Architecture index

The current executable architecture is documented in
[`ALPHA-ARCHITECTURE.md`](ALPHA-ARCHITECTURE.md).

The repository combines six concerns:

1. project state in inspectable JSON;
2. operator skills and reviewer prompts;
3. deterministic static generation;
4. validation/evidence probes;
5. authenticated approval-event contracts;
6. CI workflows.

Only the Corporate/Brochure static generation path is implemented as a
functional Alpha. Deployment, monitoring and a hosted product runtime remain
outside the implemented boundary.
