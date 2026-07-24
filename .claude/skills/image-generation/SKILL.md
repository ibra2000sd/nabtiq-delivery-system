---
name: image-generation
description: Capability skill. Generates assets STRICTLY from approved image-manifest slots and records provenance (master + derived crops + hashes + truth_label). Use for "generate the images". Never generates an unplanned/incomplete slot, never fabricates documentary content, never embeds text.
---
# image-generation
For each `status:approved` slot, generate the asset, derive desktop/mobile crops at the focal point, write
`image-provenance` (generator+version, prompt, seed, master+crop hashes, truth_label). A `documentary` slot
must map to the real `documentary_source`. Reviewed by the visual-qa reviewer + `image_plan_check` reconcile.
