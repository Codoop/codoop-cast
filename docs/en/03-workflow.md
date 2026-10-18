# Workflow and data conventions

[English](03-workflow.md) | [简体中文](../zh-cn/03-workflow.md)

This describes conceptual contracts; module implementation refines signatures/fields. Use `schema_version` consistently. Structured artifacts are formal inputs; do not parse chat history as the handoff format.

The architectural baseline for independent inputs, stable IDs/revisions and semantic scripts versus precise timing is the [skill contract](13-skill-contracts.md). Topic content determines visuals/animation. HTML is preferred without fixing every shot in advance.

## Independent and combined use

Full flow: topic → material/evidence → report → narration → storyboard → segmented speech → speech review → alignment → scene timing → rendering.

Valid entry points include supplied reports for writing, scripts for speech, audio plus transcript for alignment, and complete packages for rendering. Storyboard planning does not require audio durations; final timing requires actual final audio/alignment. Sequential execution is sufficient initially.

## Project artifacts

Follow the [project layout](20-project-layout.md): `cast-project.json`, and `research/v001`, `script/v001`, `storyboard/v001`, `assets/v001`, `voice/v001`, `subtitles/v001`, `scenes/v001`, `exports/v001`, created on demand. Do not use obsolete draft names `project.json`, `audio/`, `alignment/`, `renders/` or `plan.json` as defaults for new projects.

Shared environments, models and voice profiles stay in the private data root. Projects retain used content versions; final exports include the complete `production/` package.

## Key objects

| Object | Required information |
| --- | --- |
| Project | ID, schema version, language, aspect, fps, selected valid artifact versions |
| Source | ID, URL/path, title, publication date, retrieval time, retained text |
| Claim | Conclusion, source IDs, evidence, uncertainty/conflicts |
| ScriptSegment | Stable ID, display text, spoken text, source claim IDs |
| VoiceProfile | ID, reference audio/text, engine/model version, defaults |
| AudioSegment | Paragraph ID, audio path, samples/rate, effective settings, review state |
| Alignment | Paragraph ID, word boundaries, cues, mappings, anomalies |
| Scene | ID, related paragraphs/words, visual template, assets, key points |
| Timeline | Final audio, captions, scene/avatar tracks, profile and versions |
| Task | Input versions, stage states, errors, outputs, cache identity |

Display text such as a written year may have a TTS-specific spoken form. Preserve the mapping so captions retain meaning and align with actual pronunciation.

## One timeline

- Use WAV/PCM narration during editing; encode on export.
- Compute segment duration from real sample counts/rate, including inserted pauses.
- Add each segment's final-track offset to its local alignment times.
- Store absolute boundaries; derive frames from them rather than accumulating rounded segment durations.
- One paragraph may have several cues; one scene may span several cues.
- The last frame must cover narration's end. Check sync after composition/encoding.
- Changing speed, trims or pauses invalidates alignment and dependent timelines.

## Versions, reuse and recovery

Task states: `pending → running → succeeded / failed / cancelled`. Changed inputs mark corresponding results `stale`; reruns create new records. After unexpected exit, mark unfinished running attempts interrupted and preserve failures/successful outputs.

Cache identity includes content digests, model/rule/engine versions, effective parameters and voice-profile version. Rendering additionally depends on template, fonts, media hashes and profile. Filenames alone cannot establish reuse.

| Change | Rebuild scope |
| --- | --- |
| One script passage | Its speech/alignment; review scenes; recompute following offsets/video |
| Voice configuration | Affected speech, alignment, timeline, video |
| One asset | Affected visuals/video; reuse speech/captions |
| Caption style | Caption display/video, without new speech |
| Report facts | Mark downstream writing for review; invalidate relevant downstream results after confirmation |

A segment retry does not imply encoding only that video section: the first version can reuse intermediates and render the complete video again.

Write candidates first, validate, then update current selections. Cancellation preserves previous successes. Concurrent tasks use separate IDs/directories.

2026-10-17: single-project produce planning/state, version pinning and assembly were connected; see [workflow execution](23-produce-running.md). Sequential agent-driven batch work later added failure isolation, pause/cancel, explicit recovery and versioned reporting; see [batch](24-batch-running.md), superseding earlier unimplemented-batch notes.
