# Batch queue usage

[English](24-batch-running.md) | [简体中文](../zh-cn/24-batch-running.md)

Added 2026-10-17 inside produce, not a duplicate orchestration skill. The host runs each project's single-project workflow; the queue retains state/handoffs using stdlib, without new models/search services/daemons.

## Layout/names

```text
<selected-batch>/
  cast-batch.json
  projects/
    project-<12-character-id>/
      cast-project.json
      research/v001/
      script/v001/
      ...
  reports/
    v001/batch-report.md
    v002/batch-report.md
  .cast/locks/
```

One item per content project. New topics get stable ASCII directories and topic display names; users need not name files. Existing projects are referenced, not moved. Place the batch outside an individual project; versions/run states remain independent.

cast-batch.json stores batch/mode/item/project identity/location, target/topic, shared/item brief snapshots, state/history/attempts/errors/output pointers. Prefer batch-relative pointers, including `../` to explicitly selected outside projects; cross-drive Windows pointers are absolute. Unlike project pointers, package assets cannot escape package roots. Moving a batch must preserve external relations; absolute cross-drive references do not migrate automatically.

`schemas/cast-batch.schema.json` is independent of the eight video objects; do not put it inside one video's production package.

## User entry

Accept several topics or projects to continue. The agent saves real requirements, not user-edited JSON. `--brief-file` retains actual shared voice/aspect/resolution/audience/duration/web constraints, with per-item overrides where requested. Do not invent missing preferences. Recovery reads saved briefs, not chat memory alone.

```text
batch create --directory <batch> [--name <display-name>] [--brief-file <shared.txt>]
batch add --directory <batch> --topic <new-topic> [--brief-file <item.txt>]
batch add --directory <batch> --project <absolute-project-path> [--target exports] [--force voice]
batch next --directory <batch>
batch status --directory <batch>
batch defer --directory <batch> --item <item-id> --message <cause> [--needs-input]
batch retry --directory <batch> --item <item-id>
batch pause --directory <batch>
batch resume --directory <batch>
batch cancel --directory <batch>
batch report --directory <batch> [--output <new-report.md>]
```

Relative `--project` resolves from cwd; agents should prefer absolute paths. Brief contents are copied at creation/enqueue, so later source-file edits do not alter saved plans. Changed specifications need an explicit new batch, appropriate project reuse/force scope and retained old records.

## Execution/recovery

Next hands out at most one active project/run_id. Repeated calls return the same claim/run without launching duplicate business work. The agent executes skills, validates/registers/checkpoints; the queue observes completion, stores links and advances. Valid existing outputs can satisfy targets directly.

Next does not start workers or make a queued plan into a finished video. Default execution is sequential, without multiple agents contending for GPU. The host still researches/writes/designs/calls real tools.

Failures/missing input retain causes. Release a slot only after confirming no running step, then continue independent authorized items. Consolidate necessary questions instead of blocking everything unnecessarily. Retry is explicit/bounded: reuse a valid run; changed inputs retain run_history and create a new plan. Changed completed projects become needs_replan, not silent reruns.

Running stages cannot be deferred directly. Reconcile/cancel/fail through their skill first. Missing project/state keeps the active slot by default. Only after verifying the actual worker stopped may the agent use `defer --worker-stopped` with its cause. This is a caller assertion, not an automatic OS-process audit, and cannot bypass a known running step.

Pause prevents new work without killing active tasks. Cancel removes pending items, leaving active work visible for real reconciliation. Resume changes mode only; cancelled items need retry. Modes persist across chats.

## State/reporting

Command status=ready means execution succeeded; inspect batch_state/item states.

| Item state | Meaning |
| --- | --- |
| pending | Awaiting work |
| active | Current project, at most one |
| succeeded | Target completed with current valid evidence |
| failed | Concrete failure, retry after diagnosis |
| needs_input | Missing necessary information |
| needs_replan | Project/selections/files changed |
| cancelled | Not automatically resumed |

Complete means all succeeded; needs_attention means pending work was processed but unresolved items remain. Reports use new reports/vNNN/batch-report.md and preserve history, listing actual successes/causes. Videos remain in their project exports; do not duplicate them just for reporting.

## Validation

- Twenty-two queue tests/one schema-state contract added; 141 then passed (101 ordinary/40 contracts).
- Coverage: new projects, two reused exports, single/repeated claims, failure continuation, duplicate identity, pause/resume, cancellation, run retry, running-step protection, project changes, cross-drive pointers, missing-worker assertions, brief snapshots, report history.
- Real batch: accepted 43.73-second portrait subtitle-timing video and imported accepted 72-second landscape video. The latter passed eight schemas/cross-file checks.
- Both were recognized by next as valid results, ending 2 succeeded, with no new speech/rendering; summary generated.
- This real demonstration proves multi-project reuse/queue bookkeeping. New-topic/failure cases were deterministic tests, not a fabricated claim of multiple fresh end-to-end videos.

Pending: fresh-topic batch content quality, long host interruptions, more hardware/native hosts. This is not unattended background service/posting. [Automatic assets](26-agent-assets.md) are now connected; release licensing inventory still needed completion at this stage.
