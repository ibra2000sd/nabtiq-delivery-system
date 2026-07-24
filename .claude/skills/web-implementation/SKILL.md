---
name: web-implementation
description: Capability skill. Builds the candidate site — semantic HTML, server-first, progressive enhancement, RTL via CSS logical properties, responsive art-directed <picture> (AVIF/WebP, no SVG-before-raster hero), theme/locale bootstrap, forms with Constraint-Validation + accessible errors + consent gating. Use for "build the site / implement the page". Reviewed by accessibility + performance + visual-qa; NEVER self-approves.
---
# web-implementation
Render each page from the content pack + image-manifest + design tokens. The LCP hero paints an approved RASTER
first (fetchpriority=high) — never an SVG placeholder that swaps (first-paint flash). Direction with logical
properties, not left/right. Analytics is consent-gated (PDPL). A tiny reference renderer is scripts/build_site.py;
the runtime first-paint check is probes/first_paint_probe.mjs (Playwright).
