# Single-project workflow skill usage

[English](23-produce-running.md) | [简体中文](../zh-cn/23-produce-running.md)

Added 2026-10-17: `codoop-cast-produce`. In a content directory the user states a goal; the host invokes independent skills, reusing accepted artifacts and continuing missing/affected stages. No new web service, scheduler or model.

## Responsibilities

The agent understands intent, researches/writes, plans/designs, calls speech/alignment/rendering and reviews results. Local produce commands deterministically plan, pin versions, retain progress/failures and assemble packages. A plan is not autonomous model-driven video creation.

Independent imports remain entry points: an explicit script, speech or subtitle package does not require recreating upstream stages. In the original implementation assets lived in scene manifests/files and no unimplemented asset skill was mandatory; the later [automatic asset stage](26-agent-assets.md) extends this.

## Plans

Current default dependencies: research → script → storyboard → assets; storyboard + assets → scenes; script → voice → subtitles; scenes + subtitles → exports. A valid selected intermediate can cut off upstream execution. Inspect current selections/registration, not the largest version number.

```text
produce plan --directory <project> [--topic <topic>] [--target exports] [--force voice]
produce status --directory <project> --run <run-id>
produce start --directory <project> --run <run-id> --stage <stage> [--job <task-id>]
produce assemble --directory <project> --run <run-id> [--output <new-assembly>]
produce checkpoint --directory <project> --run <run-id> --stage <stage> --version vNNN [--job <task-id>]
produce fail --directory <project> --run <run-id> --stage <stage> --message <cause> [--job <task-id>] [--needs-input]
```

Topic is context, not permission to relabel an old video as new content. Use a new project or explicit forced research for a new topic. `--force voice` rebuilds speech/captions/export while retaining unaffected prose/visuals. Targets may stop at research/writing.

Partial/invalid inputs require review, repair/completion or explicit new imports rather than silent success/deletion. Start records execution intent, not proof a worker launched. Inspect real jobs/logs before retrying a running step.

## Storage/state

```text
.cast/runs/<run-id>/
  plan.json      # immutable plan/stages/reuse decisions
  state.json     # versions, hashes, job IDs, attempts, events
.cast/work/<run-id>/
  assembly/      # temporary selected inputs
  <checks-and-previews>
exports/vNNN/
  video.mp4
  production/
  video-qa/
  version.json
```

Hash the plan. Reused/completed stages pin selections, registration manifests and actual files. Changed selections/dependencies/content produce needs_replan rather than silently mixing new inputs.

Command `status=ready` means successful inspection. Read workflow_state: pending/running/failed/needs_input/needs_replan/complete. Checkpoint requires a started stage, registered ready output and exact plan dependencies; it selects the result. Final exports additionally need a rendered report matching the actual MP4 hash. This does not establish factual correctness/editorial approval.

Retain concrete failure/job IDs; recover through the owning skill without rebuilding valid upstream work. New outputs use new versions. There is no process resurrection/OS monitoring. Recover interruptions before progress registration from real private jobs/logs, not assumptions about state files.

## Assembly/export

While exports is running, assemble selected scenes/subtitles:

1. Recheck versions, files and selections against the plan.
2. Require identical script objects, not just similar prose.
3. Check real samples/rate and available alignment audio digest.
4. Copy declared core JSON, HTML, media, audio, captions/checks only; reject conflicting content at one path.
5. Write a new indexed assembly, then use existing compile/check/render.

Specialized validation and agent editorial review remain necessary. Assembly neither plans visuals nor invents audio/timing.

## Actual run

Continued the topic “Why subtitles need a timeline” from accepted script/v002, voice/v001 and subtitles/v002 without new search/writing/speech/alignment. Run `888a0066af874c868d3234a41f1cfcfc`:

- Reused script/subtitles, preserving audio SHA-256.
- Authored three topic-specific scenes: appearance timing, cue cards and timing review after voice changes. Registered storyboard/v001 and scenes/v001; not a universal three-page template.
- Silent preview, actual timeline and repeated-seek checks passed; encoded-caption frames stayed in bounds/clear of avatar.
- Exported 1080×1920, 30fps, ~43.73-second H.264/AAC exports/v001/video.mp4 with full decode, registration/checkpoint and complete state.
- A new plan reused the export without new speech/render tasks.

This proves continuation from real intermediates, not a fresh all-stage content run. New-project expansion had deterministic tests; existing work was intentionally not regenerated. New visuals were initially an unreviewed draft, not automatically editorially approved.

Seventeen workflow/four assembly tests were added; 118 then passed (79 ordinary/39 contracts). Coverage includes changed versions/content/plan, force scope, imports/prerequisites, bad dependencies, failures/retries, partial, duplicate starts, export proof, script mismatch, media conflicts, audio samples and preserved sources. Nine skill format checks passed.

Pending at that stage: batch/assets, more native hosts, AMD/macOS and release licensing. [Pronunciation alignment limits](22-script-audio-adapter.md) still apply; orchestration cannot bypass them with fabricated captions. Local delivery only, no automatic posting. Later [batch](24-batch-running.md) added isolation/pause/cancel/recovery/reporting and superseded pending-batch notes.
