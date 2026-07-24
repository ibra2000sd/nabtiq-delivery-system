---
name: tech-architecture
description: Capability skill. Selects the stack via a scored decision matrix, records ADRs, models content, plans framework isolation (anti-lock-in), and selects the PROJECT PROFILE (Corporate/Commerce/Authenticated/Regulated). Adopts nothing merely because it is fashionable — every choice cites the Deliverable-G research matrix. Use for "choose the stack / ADR / content model / which profile".
---
# tech-architecture
Emit `adr/*.md` + `content-model.json` + the chosen `profile`. Decision matrix scores maturity, browser support,
a11y, security, performance, ops complexity, maintainability, portability, cost, 10-year migration risk. Prefer
semantic HTML + server-first + progressive enhancement. Direction via CSS logical properties; no framework lock-in.
