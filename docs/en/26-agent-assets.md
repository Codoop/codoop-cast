# Agent-managed assets

[English](26-agent-assets.md) | [简体中文](../zh-cn/26-agent-assets.md)

Users describe a video/visual without managing directories, manifests, prompts or file copies. `codoop-assets` is automatically invoked and also supports standalone collections.

## Selection/preparation

Infer requirements from storyboards/scenes and reuse suitable existing material. Create suitable diagrams/charts/decoration locally in HTML/SVG. Use available host image generation for needed raster art and inspect actual results. Without generation, prefer a suitable local illustration; essential exact photos/footage require an explicit missing-input report, not fabricated retrieval.

No added diffusion model or mandatory subscription. Record real origins/known usage terms for external material; unknown licenses are not verified. Generated pictures illustrate, rather than serve as authentic event images/evidence. Visual text follows shared language settings.

## Files/versions

Final collections live in project assets/vNNN with assets.json and `media/<sha256>.<extension>`. Shared codoop-cast-data holds environments/models/tools/voices/engine tasks, not one video's media library.

The agent writes draft manifests in `.cast/work/<task-id>/` with stable IDs, actual source files, origins/usage. Optional metadata includes generator, prompt, author, terms, source URL/time. Copy actual bytes and hash them; identical content/extensions share one file per collection. Replacement preserves semantic IDs/collection identity and increments revision in a new directory.

```text
assets build --manifest-file <draft.json> --output <new-assets-version>
assets build --manifest-file <draft.json> --previous <old-assets.json> --output <new-assets-version>
assets validate --assets-file <collection>/assets.json
assets attach --assets-file <collection>/assets.json --package <mutable-scene-package>
```

No new model environment. Manifest instructions are in the asset skill's references/execution.md. Empty collections are complete for code-only visuals; extra images are unnecessary.

Attach copies into mutable scenes, rejecting registered versions/conflicts. The agent updates storyboard/scene references, resource paths/revisions, indexes, validates and previews. CLI does not infer editorial intent or change audio/captions.

## Workflow

Add storyboard → assets, with scenes depending on both. Audio/captions keep their independent branch. `produce plan --force assets` reuses the storyboard/audio/captions, rebuilding media/scenes/export. Pure visual styling can force scenes and reuse assets.

Existing registered scene packages/old plans remain usable without forced migration. New assets register actual storyboard dependencies; scenes register storyboard/assets so changed collections invalidate downstream content.

Managing handoffs does not mean every host has image generation, search or license verification. The agent checks real tools; final quality still requires previews/video checks.

## Shared data

codoop-cast-data is the private root; this machine selected E:/codoop-cast-data, but the name can vary. Windows defaults to `%LOCALAPPDATA%/codoop-cast`; CODOOP_CAST_HOME or --root selects another location. Reuse one root, not one per topic.

It holds private Python, speech/alignment models, browsers/FFmpeg, profiles, caches and engine tasks/logs. Separate code upgrades do not redownload everything; multiple projects share resources. Deletion can lose voices/tasks and require downloads. No migration/uninstall command is implemented; changing a path does not move data.
