---
name: studio-delivery
description: Conductor for an internally operated Corporate/Brochure Studio Alpha. Turns client files and an existing domain into verified strategy, native bilingual content, a creative direction, responsive still/video assets, a governed design system, a deterministic build, and release evidence. Use for "build this client website", "طور موقع العميل", or a full studio delivery.
---
# studio-delivery

Run delivery as stage contracts. Do not jump directly from raw files to code.

1. Scaffold with `scripts/new_project.py`; choose URL routing explicitly.
2. Inventory files with `scripts/intake_files.py`. For an existing public site, dry-run
   `scripts/crawl_site.py`, then request operator permission before `--execute`.
3. Produce and review the truth ledger. Unsupported claims remain blocked.
4. Produce `site-strategy.json`, page architecture, Arabic/English copy, and SEO. Both languages
   are authored for fluency and reference the same approved facts.
5. Produce one selected `creative-direction.json`, `design-tokens.json`, `image-manifest.json`,
   `motion-spec.json`, `generation-plan.json`, and `video-manifest.json`.
6. Dry-run media requests first. Still generation uses the configured image provider; video
   generation is allowed only after a human approves the start frame. `--execute` means external
   network use and spend; never infer that authorization.
7. Build with `scripts/build_site.py`. Run `scripts/run-checks.sh <project> build`.
8. Request fresh content, visual, motion/accessibility, and migration review. Human aesthetic
   approval and deployment authorization remain mandatory.

The deliverable is a rebuilt static site plus source contracts and evidence. It is not a
customer-facing prompt-to-site SaaS and it never self-publishes.
