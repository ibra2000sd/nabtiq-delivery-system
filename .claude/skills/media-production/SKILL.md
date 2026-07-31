---
name: media-production
description: Executes governed still and video asset production from approved manifests. Supports OpenAI image generation and Luma Ray video generation through explicit-execute provider adapters, then produces responsive WebM/MP4/poster deliverables with hashes and decode evidence.
---
# media-production

Read `generation-plan.json`, media manifests, and the approved creative direction. Start with the
dry-run commands in `scripts/media_pipeline.py`; inspect payloads and budgets. Do not use `--execute`
without operator authorization because it performs external requests and may incur cost.

Still frames use `OPENAI_API_KEY` from the environment. Luma video uses `LUMA_AGENTS_API_KEY`;
a human-approved start frame is mandatory. Never place either value in JSON, logs, source, commands,
or the ZIP. Preserve provider generation ids in the append-only job record, download outputs promptly,
then transcode to WebM and MP4 and create posters. Update hashes, seal the manifest, and run
`video_asset_check`. Documentary media cannot be generated.
