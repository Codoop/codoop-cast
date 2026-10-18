---
name: codoop-video
description: Compile actual audio alignment and HTML scenes into a synchronized local MP4. Use for final video checks, export, aspect/resolution/caption/avatar adjustments and selective re-rendering.
---

# Video

Before producing content, read the shared [production settings](../codoop-setup/references/production-settings.md) for language, aspect, resolution, fps, captions and avatar configuration. Follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Resolve the plugin root two directories above the real location of this SKILL.md, following discovery links. Run `<plugin-root>/scripts/cast.ps1` on Windows (or a compatible Python with `<plugin-root>/runtime/codoop-cast/cast.py`). Global `--root` precedes the command; reuse the user's data root. Never hard-code maintainer paths. Read [execution](references/execution.md) and the applicable JSON schemas in `<plugin-root>/schemas/` before authoring artifacts. Agent performs structured edits; users should not need to edit JSON or install dependencies manually.

1. Accept a local indexed package with script, video-script, assets, scene, output-profile, audio and alignment. These can originate outside this plugin if they satisfy the schemas. Missing real speech/alignment is a targeted missing input; never fabricate final timestamps or call a visual draft a finished video.
2. Check exact artifact revisions and audio identity. Prefer display_text-based alignment. If earlier planning uses different paragraph IDs from an external narration handoff, explicitly reconcile matching paragraphs and update references before compiling; matching text alone does not authorize stale references. Do not regenerate unrelated upstream content.
3. Run `video compile` to a new self-contained directory. Only use `--accept-reviewed-alignment` when the user has already reviewed this exact audio/alignment and accepted its known warnings; do not use it to suppress unknown failures. Invalid timing is never overridden.
4. Run `video check`, inspect screenshots and render diagnostics, then `video render` to a new MP4. Use the shared setup skill for missing authoring/video dependencies; external audio does not require installing GPT-SoVITS. Narration sample positions determine scene/event/subtitle timing; the renderer never synthesizes speech.
5. Return MP4, editable package and checks with any material limitation. Inspect layout and listen to synchronization. Automated checks cannot prove facts, pronunciation or every frame's readability. Existing user approval remains valid unless relevant inputs changed.
6. For revisions, copy the project, change only requested artifacts and their revisions/references, explicitly re-index, compile and render. Profile controls aspect/resolution/fps, subtitle style and avatar geometry. HTML must implement these controls. Avatar media is a scene-authoring responsibility; the current default is a placeholder, not a lip-sync avatar generator.


## Content project

Before reading or writing task artifacts, follow the shared [project layout](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Use the user-selected content project, explicit current versions and canonical stage/file names. Keep shared environments and voice profiles in the configured data root. Existing external packages remain valid inputs; do not silently migrate them. Initialization-only setup does not require creating a content project.
