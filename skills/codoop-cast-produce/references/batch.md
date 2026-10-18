# Sequential batch production

Use this mode when the user requests multiple topics/projects or explicitly asks to continue a batch. The host Agent drives the queue and executes the existing single-project workflow; batch commands do not call an LLM, launch a business task or create a daemon. They need no extra environment/model installation.

## Collection and files

The user-selected collection folder is outside individual content projects. It contains cast-batch.json, optional projects/project-<12-hex-id>/ for new topics, reports/vNNN/batch-report.md, and .cast/locks/. Each content project retains cast-project.json, its own stage versions and .cast/runs/. Do not flatten several topics into one script or share mutable artifact copies between projects.

Existing projects can be explicitly referenced without moving/copying them. --project accepts a normal filesystem path, resolved against the command's working directory; use an absolute path when possible. project_path in the batch file is relative to the collection when possible, including ../ for explicitly referenced external projects. Another Windows volume uses an absolute pointer. These are explicit project references, not permission for asset paths to escape their production packages. Pin each project_id and reject duplicate paths/identities, including copied folders sharing an identity. Moving external projects may require a new correctly referenced batch; do not edit stored identities to hide a mismatch.

```text
batch create --directory <collection> [--name <display-name>] [--brief-file <utf8-request-file>]
batch add --directory <collection> --topic <new-topic> [--name <display-name>] [--target exports] [--brief-file <utf8-item-request-file>]
batch add --directory <collection> --project <existing-project> [--target exports] [--force voice ...]
batch next --directory <collection>
batch status --directory <collection>
batch defer --directory <collection> --item <item-id> --message <specific-cause> [--needs-input]
batch retry --directory <collection> --item <item-id>
batch pause --directory <collection>
batch resume --directory <collection>
batch cancel --directory <collection>
batch report --directory <collection> [--output <new-report.md>]
```

Agent creates the collection/entries from the user's actual task and paths. Persist actual shared requirements (resolved voice ID, aspect/resolution, audience, target duration and source constraints where specified) with --brief-file on create; add a per-item brief where requirements differ. These are saved text snapshots, not executable commands. Read both when continuing after an interruption; item-specific requirements override only explicitly conflicting shared requirements. The user need not write these files. Do not invent unspecified preferences. Changing the original brief file does not change the saved queue; use a new explicitly planned batch for changed specifications instead of silently editing an active queue. Do not invent extra topics to fill a queue or require the user to edit JSON. If the batch already exists, inspect and continue it instead of overwriting it. A supplied topic creates a new project folder with the topic as display name; the stable folder suffix avoids collisions and unsupported filename characters.

## Agent execution loop

1. Read batch status and pending user instructions. If mode is paused/cancelled, do not start new work. Existing running jobs remain visible; a pause permits an already-started job to finish but does not authorize more stages. A cancel requires stopping actual jobs through their owning skill when possible, then reconciling produce state. Queue cancellation itself does not kill a Python/FFmpeg process.
2. Call batch next. A pending item gets a persisted produce run; a ready final artifact can be reused immediately. action execute means continue that run with the single-project instructions. action continue returns the same active item/run, not a second worker. Only one item is active per queue. action idle means no project should be started from this response.
3. Execute that project's available produce steps, preserve its actual task IDs, validate/register/checkpoint outputs. Previously accepted text, voice and style choices remain valid in their stated scope; do not ask the same question for every project. Missing creative content is authored by the Agent through the relevant skill.
4. Once produce reaches complete, batch status/next records success and the target version. Then continue the next pending project. Do not stop the entire batch merely because the first video succeeded. Inspect enough final evidence per project to avoid carrying a layout/timing error across the queue.
5. For a material failure, first record produce fail and reconcile any running job. Batch status releases the slot after it sees failed/needs_input/needs_replan with no running steps. If a necessary input is missing before a stage starts, batch defer records the cause directly. Continue independent pending projects and retain unresolved entries for the final report. Ask for needed information once, grouped when useful, while continuing unrelated authorized work.
6. Retry is explicit and bounded: inspect the cause, make a supported targeted repair, then batch retry for that item. If the existing plan is valid, its run/history is reused; if it needs re-planning, retain the old run ID in history and create a new plan. Do not repeatedly requeue the same unresolved failure. A completed project's later edits mark it needs_replan without silently regenerating or rerendering it.
7. Produce a batch report after all executable requested items have been handled. It lists successful target links and actual unresolved causes. Default exports reports link video.mp4; earlier targets link the relevant readable artifact. Reports use a new reports/vNNN/batch-report.md and never overwrite a prior report. Return the report and relevant videos; no social-platform posting is implied.

## Stop/recovery details

status ready is command success, not batch success. Read batch_state and per-item states/counts. Batch states are running/pending/paused/cancelled/complete/needs_attention. Item states include pending/active/succeeded/failed/needs_input/needs_replan/cancelled. needs_attention means all executable pending items were handled but unresolved items remain. An empty newly created queue has no work.

Pause/cancel persist across chat interruptions. Resume only changes queue mode; cancelled items remain cancelled until explicit retry. Do not restart cancelled work merely because the queue was resumed. If actual worker state is unknown (missing/corrupt project/run), retain the active slot. Only after checking task records/processes and confirming no worker is running may the Agent use `batch defer ... --worker-stopped` with the concrete reason; this is an explicit caller assertion, not an automatic process check. It cannot bypass a known running produce step. Never add this flag merely to skip a busy project.

A moved/missing project, changed identity, modified registered output or changed selected dependencies is not permission to silently substitute another project. Fix the reference/restore the project or report it unresolved. Whole-collection portability requires preserving external relative relationships; absolute cross-volume pointers are machine-specific.
