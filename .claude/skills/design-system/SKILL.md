---
name: design-system
description: Capability skill. Produces DTCG design tokens (SUPPORTED token types only — color incl. OKLCH, dimension, typography, spacing, motion) + component contracts. Theming via the DTCG Resolver. Use for "design tokens / theme / Light-Dark / components". Direction (RTL/LTR) is NOT a token — it is implemented with CSS logical properties; image focal points live in the image-manifest, not tokens.
---
# design-system
Emit one `design-tokens.json` with DTCG-style base tokens and `semantic.light`/`semantic.dark` mappings.
The implemented renderer resolves token leaves to CSS custom properties. Include colour, typography, layout,
radius, motion and the four glass depths: nav, surface, deep and luminous. Declare solid contrast pairs for
deterministic checking and mark translucent/image pairs as hybrid. Direction remains in `site-map.json` and
CSS logical properties; image focal points remain in `image-manifest.json`.
