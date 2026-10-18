# Independent skills and workflow handoff contracts

[English](13-skill-contracts.md) | [简体中文](../zh-cn/13-skill-contracts.md)

> Historical architecture/validation record. Current state: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

Baseline: 2026-10-17, when setup/voice/subtitles had local alpha implementations and the rest were planned, without placeholder skills. This superseded grouping subtitles under video. Speech-task or external audio/transcript input did not yet imply complete-package orchestration.

## Separation principles

Each skill completes an independently requestable task with inspectable files. External inputs do not require upstream execution. Exchange structured files rather than chat history/machine paths. Obtain only necessary missing inputs, without automatically repeating earlier stages.

Read standard packages, adapt acceptable external files to internal objects, retain origin/conversion records, and provide usable downstream files. Missing provenance/identity/style stays unknown, not invented.

## Boundaries

| Skill | Independent input | Output/handoff | Excludes |
| --- | --- | --- | --- |
| setup | Feature/missing-capability report | Private environment/resources/checks | Content or installing every feature |
| research | Topic, own material, search constraints | report.json/report.md, claim IDs/evidence/sources/conflicts/unknowns | Narration/video |
| script | External report/material or report.json | script.json/readable prose, paragraph IDs, display/spoken text, claims | Storyboarding/speech |
| storyboard | External script or script.json | video-script.json/review, narration refs, visual intent, screen text, asset needs, anchors | Final seconds/all asset creation |
| assets | Asset description, supplied media, storyboard needs | assets.json/local files, IDs/origin/generation/hash/dimensions/use limits/state | Rewriting speech/unrelated regeneration |
| voice | Reference/saved voice and external text | WAV/task manifest/original-spoken forms; later paragraph/range handoffs | Caption timing/visuals |
| subtitles | Audio/transcript or speech task | alignment.json/SRT/checks, words/mappings/hashes/offsets | Rewriting/re-reading/shot content |
| scenes | Storyboard or external visual description plus media | Seekable HTML/package/preview, element IDs/anchors/layout/resource dependencies | TTS/fact changes/final voiced export |
| video | Standard package or scenes + audio + timing/captions | Resolved timeline/preview/MP4/checks/profile/input versions | Automatic research/writing/images or replacing accepted content |
| produce | Topic or intermediates + desired target | Coordinate implemented skills, project index/plan, package/video | Duplicated module logic |

All names above use the `codoop-cast-` prefix. Scenes create visuals; video binds timing and exports. Assets can prepare one image or reuse local material without mandatory generation. Host image generation depends on tools; record origin/network use, not a blanket local-capability claim.

Voice later gained `--script-file`, retaining original identity. Paragraphs may span TTS chunks; real alignment restores original paragraph ranges. Chunk IDs are not paragraph IDs: [adapter](22-script-audio-adapter.md).

## One content hub, multiple outputs

`video-script.json` is the editable content hub referencing pinned scripts/assets/scenes/profile. Narration lives in script only; do not duplicate contradictory bodies. Standalone delivery can bundle dependencies without a global database.

The storyboard holds intent/semantic anchors; the exact timeline is compiled from selected audio/alignment. Version separately. Users edit content, not derived seconds. A future manual override must distinguish relative offsets/fixed times and report invalidated overrides.

Package paths are relative/contained; execution returns accessible absolute paths. Objects have stable IDs, schema_version and revision. References identify artifact/revision/object and necessary digest, not filenames alone.

Logical handoffs contain execution status, task ID, primary files, dependencies, anomalies, unresolved inputs and next capabilities. Successful planning is separate from render readiness: missing media can coexist with a completed plan. Suggested next work is not authorization.

Initially schemas check required fields/references/revisions; explicit adapters import external files. This architecture is not a claim that every proposed CLI/schema field is already available.

## Time anchors

Animation can anchor to scene start, paragraph start/end, particular words and relative offsets. Word anchors require paragraph ID plus range/token ID; a phrase alone is ambiguous when repeated. Removed/edited targets become unresolved, not silently relocated.

Plan scalable visuals first; bind actual timing after TTS/alignment, then compile video. Cues and shots are not one-to-one. External scenes with reliable timing can render independently. Missing anchors/durations need input, not invented precision from character count.

## Minimal rebuilds

| Change | Update | Reuse |
| --- | --- | --- |
| Research claim | Flag related prose/scenes for review, then affected downstream work | Unaffected claims/paragraphs/assets |
| Narration paragraph | Related speech/alignment/anchors/following offsets | Unrelated voice/visual content |
| Image requirement | Specific asset, referring scenes/video | Prose/audio/caption timing |
| Scene style/animation | Scene/video | Media/audio/alignment |
| Caption style/avatar position | Layout checks/video | Research/prose/audio/word times |
| Aspect/resolution | Scene/caption/avatar relayout/video | Content/audio; unsuitable crops may need alternate images |

Create revisions and retain accepted versions. Pure time shifts update offsets rather than speech. Reuse follows actual dependency/settings hashes. Partial reuse does not promise partial encoding; full final rendering is acceptable initially.

## Implementation order and updates

Start with minimal schemas/examples for script, video-script, assets, scene, alignment and timeline, validating IDs on the 72-second sample. Test local alignment/HTML and complete script-to-MP4, then deliver independent storyboard/scenes/assets, followed by research/script/produce. This development order does not constrain the user's entry point. Register necessary setup features only with executable skills.

Updates on 2026-10-17: [video skills](18-video-skills-running.md) and shared authoring/video setup were implemented; [research](19-research-running.md) added report/evidence/export while writing was then pending; [project layout](20-project-layout.md) added initialization/registration/selection/dependency checks; [writing](21-script-running.md) later added source-linked validation/export/import, with voice identity still pending at that stage; [produce](23-produce-running.md) added persistent single-project planning, version pinning and assembly. Current state is in the readiness document.
