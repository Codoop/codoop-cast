# Persistent single-project runs

Use the shared Windows launcher or compatible Python with `<plugin-root>/runtime/codoop-cast/cast.py`. Reuse the data root for business tasks. produce itself uses only stdlib and adds no feature/model environment.

```text
produce plan --directory <project> [--topic <topic>] [--target exports] [--force voice ...]
produce status --directory <project> --run <run-id>
produce assemble --directory <project> --run <run-id> [--output <new-assembly-directory>]
produce start --directory <project> --run <run-id> --stage <stage> [--job <task-id>]
produce checkpoint --directory <project> --run <run-id> --stage <stage> --version vNNN [--job <task-id>]
produce fail --directory <project> --run <run-id> --stage <stage> --message <specific-cause> [--job <task-id>] [--needs-input]
```

Run IDs are 32 lowercase hex characters. `.cast/runs/<run-id>/plan.json` stores immutable stage decisions; state.json stores stage progress, version manifest hashes, task IDs, attempts and events. Root/current selections stay in cast-project.json. Status ready means the status operation succeeded; workflow_state is pending/running/failed/needs_input/needs_replan/complete. Check actual workflow_state and target artifact rather than stdout status alone.

The default dependency graph is research → script → storyboard → scenes and script → voice → subtitles, with scenes + subtitles → exports. Existing ready imported intermediates form entry points, so selected subtitles do not require regenerating a voice and selected scripts do not require researching again. Optional assets are managed by scenes/assets.json for now, not by an unimplemented mandatory assets skill.

--force invalidates the specified stage and graph descendants contributing to the target. Selected unaffected intermediates are reused. partial/invalid inputs produce a review action; they cannot silently checkpoint as ready. Agent resolves the cause or obtains necessary missing information. Reused and completed steps pin selected versions, their file/dependency integrity and manifest hashes; selection/content changes require a new plan. Actual new dependencies must match completed plan steps at checkpoint. Old registered versions remain unchanged.

--topic records the task context; changing the actual topic requires a new content project or an explicit --force research plan, rather than relabeling an existing finished video.

A new plan does not reserve output directories or start jobs. start records intent and a fresh candidate path; it is not proof that a worker started. Attach task ID when available (checkpoint/fail), and keep a local .cast/jobs reference during a long task if needed. If interrupted before recording its ID, inspect the configured data-root job records/logs rather than launching duplicates. A recorded running stage cannot be started again until its actual state is reconciled with checkpoint/fail. No automatic daemon or process resurrection is claimed.

## Stage execution

- research: codoop-research produces a report package in research/vNNN, then register it. If explicit source script/report is imported, preserve its provenance; do not manufacture a research stage just for the graph.
- script: codoop-script exports script/vNNN and registers actual research dependency when present. A known accepted script can be reused as-is.
- storyboard: codoop-storyboard imports selected script, authors the topic-specific video-script.json and storyboard.md, validates, and registers script dependency. Output-profile and assets references must be exact.
- voice: codoop-voice uses speech generate --script-file with the selected script and known voice, then registers script dependency. Reuse accepted audio when its version is unchanged. User preferences/approval in current context persist.
- subtitles: codoop-subtitles aligns the exact selected voice job, registers voice dependency (and script when used). For an external self-contained package, import it as an explicit entry point instead of claiming a nonexistent source job.
- assets: codoop-assets automatically prepares a local collection (empty is valid for code-only visuals), registers the selected storyboard dependency, and checkpoints it. Users do not manage manifests or paths.
- scenes: codoop-scenes authors local HTML/scene.json, validates and previews, and registers both selected storyboard and assets dependencies for new workflows. All CSS/JS/fonts/media must be declared local assets. Do not invent the final clock from word counts.
- exports: stage an assembly in .cast/work/<run-id>/assembly. Use produce assemble after starting exports; it copies exact script/audio/alignment/media from subtitles and video-script/assets/scene/output-profile/declared resources from scenes. Require identical script artifacts; fail on conflicting paths/content. Explicitly index, compile to exports/vNNN/production, check, render to exports/vNNN/video.mp4 and inspect video-qa. Register dependencies on the plan's selected subtitles and scenes, then checkpoint. A checkpoint requires a rendered report matching the actual MP4 SHA-256.

For semantic review or a supported local repair, preserve successful unaffected artifacts. A material audio/alignment change invalidates earlier listening/timing approval; a purely visual change does not. An unreviewed new plan can be rendered as a local draft within a full-production request; do not describe it as editorially approved. No default external publication is authorized.

## Configured output format

Run config show for the project before planning. The plan returns pinned video settings and accepts --video-config-file for a task-only patch. Carry that patch or the exact resolved output-profile into storyboard prepare. Explicit configured profile mismatches rebuild the visual branch, preserving narration and factual content; reuse media bytes where appropriate. A changed effective configuration requires a new visual plan. Checkpoints for storyboard/scenes/exports reject mismatched actual output-profile files. Old plans remain readable; do not edit registered files or silently change package settings during rendering. Full conventions: [production settings](../../codoop-setup/references/production-settings.md).
