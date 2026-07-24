---
name: art-direction-image-plan
description: Capability skill. Sets the premium art direction and motion direction AND produces the complete page-level image-manifest BEFORE any asset is generated. Every slot: why_needed, narrative_function, subject, desktop/mobile crops, focal_point, text-safe zones, Light/Dark variants, truth_label (conceptual/documentary), prohibited elements, alt (EN/AR), loading_priority, perf budget. Use for "art direction / plan the images / image manifest". Does not generate assets.
---
# art-direction-image-plan
Emit `image-manifest.json` covering EVERY page/section slot (inner pages included, not homepage-only).
Rules enforced by `image_plan_check`: a `documentary` slot needs a real `documentary_source`; fallback
must never be `svg` (first-paint flash risk); Light AND Dark variants required; focal_point in [0,1].
Prohibited: embedded text, fake certificates/flags/facilities/staff. Generation happens only after G8 approval.
