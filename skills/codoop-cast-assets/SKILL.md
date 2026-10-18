---
name: codoop-cast-assets
description: Prepare and reuse local video assets from a storyboard or visual request, track their provenance, and replace assets without regenerating narration. Invoke automatically when scenes need media; users do not need to manage files or manifests.
---

# Agent-managed assets

Follow the shared [artifact language policy](../codoop-cast-setup/references/language.md) and [project layout](../codoop-cast-setup/references/project-layout.md). Resolve the real installed plugin root two directories above this SKILL.md. Use its `scripts/cast.ps1` on Windows or `runtime/codoop-cast/cast.py` with a compatible Python; reuse the configured private data root. Read [execution](references/execution.md) for the manifest and handoff commands.

Own the material preparation work. Infer requirements from the user's visual request, selected storyboard and existing scene asset IDs. Do not ask the user to choose directories, name files, fill manifests, pick stock libraries, or manage generation prompts. Reuse relevant approved local assets first. Build explanatory diagrams, charts and decorative shapes directly in HTML/SVG when appropriate; claims and chart data must retain their actual source. A code-only video needs no external image and an empty asset collection is valid.

For raster imagery, use the host's available image-generation capability when it improves the explanation. Follow that capability's own instructions, inspect its returned image, and retain the actual local result, prompt and generator name. Do not require a particular provider, new subscription or GPU model. If image generation is unavailable, use a suitable local/code visual. If a specific missing image or exact footage is essential, report that concrete missing input rather than fabricate a retrieval or generation result. Treat generated illustrations as illustrations, not evidence or authentic event photographs. Use external media only when suitable for the authorized task and retain actual origin and usage information; do not label an unknown license as verified.

Prepare the collection with stable semantic asset IDs, local copies, content hashes, origin and usage notes. Keep detailed provenance where available. For an asset replacement preserve its semantic ID, create a new collection version, and retain the old version. Do not edit source files, approved stage versions, reference voices, narration or timing. Attach the collection to a new mutable scene working package; update dependent artifact references and revisions, index, validate and visually inspect the affected scenes. Re-render the requested export through the video skill.

In a production run register/checkpoint the assets stage with its actual storyboard dependency; scenes depend on both storyboard and assets. Report the final requested content, not a new mandatory material-approval step. Mention asset details only when they affect the user's decision or a concrete limitation. This skill can also prepare an independent collection without requiring research, TTS or a production run.
