---
name: seo-structured-content
description: Capability skill. Produces the SEO/GEO layer — entity graph, JSON-LD/Schema.org, hreflang + canonical maps, titles/descriptions, citation-ready structure. Use for "SEO / structured data / entities / hreflang". Grounded only in ledger facts; never asserts AI-answer inclusion.
---
# seo-structured-content
Write localized `seo.title` and `seo.description` into each page contract. `site-map.json` owns the paired
locale routes and `brand.json` owns the canonical origin. The renderer emits canonical, hreflang, Open Graph,
JSON-LD, sitemap and robots output; verify it with `seo_output_check`. JSON-LD reflects only grounded entities.
No cloaking, no llms.txt as a load-bearing dependency, and no guarantee of generative-engine inclusion.
