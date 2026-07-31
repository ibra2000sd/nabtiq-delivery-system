---
name: content-architecture
description: Capability skill. Turns approved strategy into a sitemap and per-page briefs — for each page: purpose, message hierarchy, required fact-ids, required image slots, CTA. Use for "sitemap / page plan / what pages do we need". Corporate/Brochure default page set. Does not write final copy.
---
# content-architecture
Produce `site-map.json` plus `pages/<id>.content.json` contracts. Every route has independent `en` and `ar`
paths and each localized page starts with a hero block. Each product/service page MUST resolve the full
essential-field set (what_it_is, applications, sourcing_role, documented_origin, quality_indicators, packaging,
trade_terms, logistics, documentation, enquiry_requirements). A page with no purpose or no required facts is invalid.
Validate routes and CTA targets with `site_contract_check`.
