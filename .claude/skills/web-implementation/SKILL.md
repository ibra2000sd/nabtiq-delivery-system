---
name: web-implementation
description: Capability skill. Builds the candidate site — semantic HTML, server-first, progressive enhancement, RTL via CSS logical properties, responsive art-directed <picture> (AVIF/WebP, no SVG-before-raster hero), theme/locale bootstrap, forms with Constraint-Validation + accessible errors + consent gating. Use for "build the site / implement the page". Reviewed by accessibility + performance + visual-qa; NEVER self-approves.
---
# web-implementation
For the implemented Corporate/Brochure profile, render with `scripts/build_site.py`. It must consume
`brand.json`, `site-map.json`, localized page contracts, `image-manifest.json` and `design-tokens.json`;
hard-coded page copy is prohibited. The LCP hero paints the approved responsive raster first with dimensions
and `fetchpriority=high`. Use logical properties for RTL, semantic HTML, no-JS content availability, reduced
motion and opaque glass fallbacks. Run build, contract, asset, SEO and browser first-paint checks; never self-approve.
