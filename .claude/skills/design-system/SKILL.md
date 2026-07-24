---
name: design-system
description: Capability skill. Produces DTCG design tokens (SUPPORTED token types only — color incl. OKLCH, dimension, typography, spacing, motion) + component contracts. Theming via the DTCG Resolver. Use for "design tokens / theme / Light-Dark / components". Direction (RTL/LTR) is NOT a token — it is implemented with CSS logical properties; image focal points live in the image-manifest, not tokens.
---
# design-system
Emit `design-tokens.json` in DTCG 2025.10 format using only supported token types. Light/Dark via the Resolver
module (no duplicated files). Component contracts list props/states/a11y roles/RTL behaviour/token bindings.
Do NOT encode text direction or image focal points as tokens.
