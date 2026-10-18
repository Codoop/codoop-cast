---
name: codoop-scenes
description: Create local HTML scenes and time-controlled animations from a video storyboard. Use for visual design, scene revisions and visual previews, independently of TTS and final MP4 export.
---

# Scenes

Before producing content, follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Resolve the plugin root two directories above the real location of this SKILL.md, following discovery links. Run `<plugin-root>/scripts/cast.ps1` on Windows (or a compatible Python with `<plugin-root>/runtime/codoop-cast/cast.py`). Global `--root` precedes the command; reuse the user's data root. Never hard-code maintainer paths. Read [execution](references/execution.md) and the applicable JSON schemas in `<plugin-root>/schemas/` before authoring artifacts. Agent performs structured edits; users should not need to edit JSON or install dependencies manually.

1. Accept an indexed package containing script, video-script, assets and output-profile. Do not require voice or alignment for visual authoring. Read the narration and visual intent before choosing layouts, diagrams, typography and transitions.
2. Author local HTML/CSS/SVG for this topic, using the rendering contract below. Images may come from user assets or an explicitly requested/available image generation capability. Record provenance, rights information and local files in assets.json. Do not silently depend on remote fonts, scripts or media.
3. Write scene.json referencing the exact video-script revision; preserve scene IDs, list actual element IDs and asset IDs, and declare supported aspect modes. All supporting CSS/JS/fonts/images must be declared assets, so the compiled package includes them. Multiple scenes may share an HTML entry.
4. Run `project index`, `scenes validate`, then `scenes check` after setup of the video feature. Inspect generated screenshots for clipping, subtitle/avatar overlap and legibility. Fix visual problems and repeat only affected verification. The illustrative preview has no narration, uses arbitrary scene durations, and cannot be exported as a final video.
5. Return scene.json, local files and preview evidence. Do not rewrite the narration or upstream storyboard to make a layout fit. Profile changes may require a new responsive layout; never stretch an incompatible design.


## Content project

Before reading or writing task artifacts, follow the shared [project layout](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Use the user-selected content project, explicit current versions and canonical stage/file names. Keep shared environments and voice profiles in the configured data root. Existing external packages remain valid inputs; do not silently migrate them. Initialization-only setup does not require creating a content project.

## Automatic material preparation

When a scene needs local media or an asset replacement, invoke `codoop-assets` as internal preparation. Reuse selected assets and let the agent create/import and track missing material without asking the user to manage it. Read its [handoff instructions](../codoop-assets/references/execution.md), attach the collection to a mutable working package, update dependent revisions and asset references, then validate. Register new scenes with their actual storyboard and assets dependencies; reuse existing audio and subtitle versions for visual-only changes.
