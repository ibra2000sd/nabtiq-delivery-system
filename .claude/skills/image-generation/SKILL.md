---
name: image-generation
description: Capability skill. Generates assets STRICTLY from approved image-manifest slots and records provenance (master + derived crops + hashes + truth_label). Use for "generate the images". Never generates an unplanned/incomplete slot, never fabricates documentary content, never embeds text.
---
# image-generation
For each approved slot, generate the source, derive desktop/mobile/social/LQIP renditions at the declared
focal point, and record provenance inside the slot (mode, generator, prompt/version, source and human review).
Store generation sources under `assets/source/`; the renderer deliberately excludes them from `build/`.
A documentary slot must map to its real source. Run `image_plan_check` and `asset_integrity_check`, then request
visual QA. Use `scripts/media_pipeline.py image ...` in dry-run mode first. Only an operator-authorized
`--execute` may call the configured provider; its API key stays in the environment.
