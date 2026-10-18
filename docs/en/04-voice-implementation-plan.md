# Voice cloning and speech skill implementation plan

[English](04-voice-implementation-plan.md) | [简体中文](../zh-cn/04-voice-implementation-plan.md)

Status: alpha implementation. V0–V4 have code and local inference validation; V5 has skills, manifests and a fallback installer, but no native-host acceptance. V6 still requires target-speaker listening and more clean-environment tests. This is the design baseline; use the [running guide](08-running-voice.md) for actual commands.

## Product and delivery principles

Experience correction: 3–10 seconds is the pinned GPT-SoVITS v2 inference check for an internal reference clip, not the maximum user recording length. Local faster-whisper small CPU/int8 transcription and automatic selection are implemented. Preserve the original audio/clip offsets; return uncertain transcription as a draft for confirmation. Automatic speaker diarization is unavailable: establish the target when multiple speakers are known.

The preparation sequence is recognition/VAD → sentence-boundary selection within engine constraints → exact clip transcript → retained original, offsets, clip and text → synthesis. Never crop audio while retaining the whole-recording transcript or infer a single speaker merely from volume. Consolidate necessary questions for multiple speakers/uncertain text. Explain too-short or unusable speech; padding silence does not create a valid reference.

The user should be able to ask, “Read this script using this voice,” and receive local audio, rather than operate a model toolkit. Normal use is reference → script → audio. Saved voices are reusable. Users need not understand models, segments, sample rates, dependencies or inference knobs. Training, fine-tuning and training-data management are excluded, including from the roadmap.

Users need not run setup first. Voice checks readiness and invokes shared setup only as needed, then resumes the original request. Setup is the plugin-wide check/install/repair entry; voice registers its dependencies without owning a separate setup. See [shared setup](07-setup-skill-plan.md).

## Confirmed conditions

The [plugin experience](05-plugin-experience.md) makes setup/voice skills, a stable CLI, on-demand preparation and clean-machine acceptance part of delivery. The functions/processes below are internal; users operate through an agent.

Follow codoop-flow's thin adapters for Codex, Claude Code and Cursor over one runtime. Verify hardware in the order Windows/NVIDIA → Windows/AMD → Mac: [compatibility](06-compatibility.md). Python 3.10 is this development setup; other backends can use separately validated private versions.

Import a recording, select/transcribe its reference and save a profile; then synthesize playable/exportable Chinese WAV locally. This module is independent and hands segment audio and precise composition boundaries to subtitles. GPT-SoVITS uses existing pretrained weights and reference-driven inference only.

Inspected machine: Windows 10 Pro 64-bit, i5-13400F, RTX 3070 Ti 8GB, approximately 32GB RAM. E: had about 77GB free at inspection; recheck before installation.

At the user's request Python 3.13 was removed and Python 3.10.11 installed at `E:\Tools\Python310`; existing 3.9 was untouched. Dependencies, models and GPT-SoVITS are in the developer's private `E:\codoop-cast-data`, not global Python. This is a local deployment record, not another user's required path.

## Scope

User capabilities: save/reuse a voice, synthesize text/files, list voices, play results, request specific passage retries in natural language, export WAV.

Internal work: environment checks/preparation, reference normalization, semantic splitting, durable tasks, audio checks/composition, retries and exact-duration manifests. These are not a mandatory user-facing menu.

Alignment/video are separate modules. Post-generation ASR quality checks need separate evaluation. Reference recognition belongs to current initialization and must not be postponed while requiring manual cropping/full transcription.

## Entry points and routing

| Skill | Responsibility | Example request |
| --- | --- | --- |
| `codoop-voice` | Store/reuse voices, synthesize, retry passages | “Read this with this voice”; “use the previous voice”; “redo paragraph two” |
| `codoop-setup` | Shared environment checks, initialization, configuration and bounded repair | “Initialize”; “check speech dependencies”; “change the cache location” |

Voice descriptions must not attract research/writing/video work. Setup is not general system maintenance. Keep SKILL.md short, conditional error/parameter details in references, and deterministic operations in scripts.

Default the profile name from the file and tell the user; naming is not a prerequisite. Use an explicitly selected voice; use the only profile automatically; ask once if multiple profiles are ambiguous. Preserve an established choice within the task without guessing another person.

Store profile ID, task ID and artifact path after completion so “last time” and “paragraph two” resolve through actual records. Ask only when multiple candidates remain.

## User flow

1. Accept reference plus script, or an existing voice plus new script. Ask only for missing necessities.
2. Validate inputs and readiness. For missing dependencies explain first-download volume/location and invoke setup within existing authorization/host permissions; otherwise generate immediately.
3. Save the profile, normalize its audio/text, and split semantically. Infer reference language from content, asking only when ambiguous. Do not require model settings or per-segment approvals.
4. Generate/check/join internally. Give meaningful long-task progress and retain retryable failures.
5. Export the complete WAV automatically. Present playback where supported, otherwise an accessible local link. Explain voice naming/reuse briefly.
6. For pronunciation/speed/passage changes, reuse the profile and unaffected successes, returning a new complete result without asking the user to select attempt IDs.

For overly long/problematic material, mixed speakers or mismatched text explain the concrete issue and obtain a usable reference/correct text. Do not silently change speaker or script. Engine-specific constraints follow the pinned version; scripts handle ordinary decodable-format conversion.

Skills are the product entry, local CLI the agent execution entry, and Python the internal interface. There is no HTTP/WebUI; native packaging still requires validation.

## Runtime structure

```text
Agent → voice skill → local CLI
                       ↓
             profiles, tasks, artifacts
                       ↓ Python adapter / local messages
             isolated GPT-SoVITS worker
                       ↓
       segment WAV → format/join → final WAV + manifest
```

- Python modules call directly. A task's isolated worker reuses its model and releases resources afterward, without a permanent service spanning chat messages.
- No ports, upstream API or WebUI. Validate direct Python inference; initially one GPU synthesis task at a time.
- The adapter exposes status, model identity and verified capabilities. Exchange line-delimited JSON, use local paths for media, and keep logs on stderr/files.
- Pin upstream commit, matching GPT/SoVITS weights and dependencies first; do not mix weight generations.
- Reference: [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS). Confirm commands, names and settings against the pinned revision before implementation.

## Files and data

The following was a maintainer-only layout proposal. Released storage follows the [plugin design](05-plugin-experience.md), with configurable private data separate from installed code. Keep personal audio/models out of source control.

```text
.venv/                         # application environment
.runtime/gpt-sovits/            # source, isolated environment, models, logs
data/voices/<voice_id>/         # original reference and normalized copy
data/jobs/<job_id>/             # texts, segments, manifests, joined WAV
data/codoop-cast.sqlite         # proposed profile/version/task/artifact index
```

Add ignores before implementing these draft locations; this plan itself creates none. E: is a developer preference, not a requirement. Other users use platform data locations or explicit settings, without system-Python/PATH changes.

The distribution uses `skills/`, `runtime/codoop-cast/` and `scripts/`. Packaged runtime code is separate from user models/interpreters/tasks. Skills locate the CLI relative to their real installed location, not the working directory.

| Object | Draft fields |
| --- | --- |
| Voice | ID/name/version, reference path/hash/text/language, engine/weights, defaults |
| Speech task | ID, profile snapshot, original/spoken text, segments, state, creation time, errors |
| Segment | Paragraph/attempt IDs, text, WAV path, rate/channels/samples, elapsed time, checks |
| Joined manifest | Segment order, selected attempts, common rate, sample boundaries, inserted silence, total samples, source versions |

Snapshot the submitted profile; later edits must not affect running tasks. Retry creates an attempt and retains prior audio rather than overwriting successes. The draft deletion design archived profiles and blocked new references while keeping past tasks/audio readable; permanent cleanup needs a separate design.

CLI JSON includes `status`, applicable `job_id`, `artifacts`, `next_action` and structured `error`. Show users results, necessary progress and actionable problems. Verify Windows arguments and Chinese/space paths before finalizing commands.

## Draft internal calls

These are responsibilities, not HTTP routes; signatures depend on adapter validation.

| Operation | Draft function | Behavior |
| --- | --- | --- |
| Engine state | `get_engine_status()` | Stopped/loading/ready/faulted |
| Capabilities | `get_voice_capabilities()` | Verified settings/reference constraints |
| Create voice | `create_voice(...)` | Import local audio/text/name/language |
| Read voices | `list_voices()`, `get_voice(id)` | List/details |
| Edit voice | `update_voice(id, ...)` | New version |
| Submit speech | `submit_speech_job(...)` | Task ID and queued execution |
| Read task | `get_speech_job(id)` | Stage/segments/paths/errors |
| Retry segment | `retry_segment(job_id, segment_id)` | New attempt |
| Export | `export_speech_job(id, ...)` | Check selections; write WAV/manifest |
| Playback path | `get_artifact_path(id)` | Registered path; entry point plays it |
| Cancel | `cancel_speech_job(id)` | Stop scheduling; finish/interrupt current inference as supported |

Validate selected local files and copy to managed storage, without upload/download endpoints. Errors include type, explanation and retry guidance. Worker messages include request/task IDs, action, arguments, progress and result/error. Read them without blocking the interaction entry, retain exit codes, identify unexpected termination and avoid duplicate generation on recovery. First-version cancellation takes effect between segments, not necessarily mid-inference.

## Segmentation, audio and recovery

- Split semantic sentence groups, with size determined by real voice tests; avoid character-level/tiny fragments.
- Pin profile/settings per task and review timbre/loudness across a retried boundary.
- Store display/spoken text separately; support explicit pronunciation edits without promising automatic correction.
- Retain raw outputs before normalizing sample rate, channels and PCM; lock the target format after validation.
- Compute joins from normalized sample counts, including silence, so subtitles need not guess pauses.
- Failed audio checks block formal export. Allow listening/retry.
- Automatically retry a clearly transient fault at most once. Do not blindly retry OOM, invalid inputs or mismatched weights.
- Preserve successful segments on crashes, mark running attempts interrupted, and resume only missing work.
- Write candidates, validate, then register. Failed export does not replace a prior success.
- Retain versions/settings for traceability; identical waveform reproduction is not promised.

## Implementation steps

| Step | Work | Deliverable/acceptance |
| --- | --- | --- |
| V0 Package/inference baseline | Three hosts, shared runtime, pinned source/weights/dependencies/reference constraints | Layout/resource lists; no training resources or technical user configuration |
| V1 On-demand setup | Shared registry, doctor/config, private environment, verified downloads/recovery, NVIDIA inference | Clean-machine short Chinese speech; voice-only preparation; preserve other settings/global environment |
| V2 Voice reuse | Import/check/default name/save/select | Survives restart; one voice is automatic, ambiguity prompts accurately |
| V3 Speech CLI | Text/files, splitting, task records, progress, retries | Three script classes succeed with stable structured I/O and hidden internal steps |
| V4 Export/recovery | Normalize/join, offsets, cancel/resume | Complete WAV per request; retry returns a new result while reusing other segments |
| V5 Skills/package | Concise triggers/references, commands, manifests/fallback install | Shared CLI resolves; voice initializes as needed; actual host tests recorded |
| V6 User journey/release | Install, first synthesis, reuse, retry, upgrade preservation | Real agent on clean environment obtains WAV; license/support/limitations documented |

Inspect each deliverable before advancing. This section records the planned order, not proof all steps were completed at authoring time.

## Acceptance examples

| Example | Checks |
| --- | --- |
| About 15 seconds of everyday Chinese | Similarity, natural pauses, no obvious omissions/repeats |
| Numbers/dates/units/English acronyms | Display/spoken correspondence and editable pronunciation |
| About one minute of explanatory narration | Continuity, levels, complete playable output |
| Invalid/silent reference | Fails before synthesis without a false success |
| One segment retry | Prior attempts traceable; unrelated files unchanged |
| Engine unavailable/OOM | Specific cause, preserved work, resumable state |
| Cancellation/restart | Explainable states; no duplicate completed work |
| First voice invocation | Detect/init missing feature and continue without manual setup |
| Same voice again | No repeated setup or request for retained reference |
| Multiple unselected profiles | Ask only for necessary choice; do not pick a person arbitrarily |
| Chinese/space paths, arbitrary cwd | Runtime resolves; inputs readable; output has usable absolute path |
| Another user/upgrade | No developer-path dependency or overwritten profiles/projects/global Python |

Naturalness/similarity are evaluated by listening, without invented objective thresholds. Record hardware, text length, output length, cold/warm runtime and peak VRAM before setting performance targets. Automated checks cover inputs, recovery, selection and sample/offset consistency; mocks do not establish model quality.

## Remaining inputs and decisions at this stage

- V0 fixes manifests/runtime location; V5 packages skills; V6 validates first/repeated clean-machine use. Developer success is not complete delivery.
- Supply a clear owned/authorized reference with accurate text. Without it, use clearly licensed examples only for the technical chain, not target-speaker similarity claims.
- Pin upstream/weights against official sources in V0.
- Set speed, pauses and splitting after V1 listening.
- Codex, Claude Code and Cursor are confirmed targets; exact versions/install commands need packaging tests.

The user authorized implementation. Unfinished release/hardware acceptance must not be marked passed.
