# Overall plan

[English](01-plan.md) | [简体中文](../zh-cn/01-plan.md)

> Historical plan and validation record. See [Alpha release readiness](29-release-readiness.md) for current capabilities and gaps, and the [installation guide](28-install-and-first-video.md) for first use.

## Goal

The product is an open-source agent plugin. Users install it and access local capabilities through skills. Packaging, initialization and usability follow the [plugin experience design](05-plugin-experience.md) and are part of each module's delivery requirements.

Turn a knowledge topic into a narrated social-media video with less repeated research, voice generation and editing. Research, writing, speech and video can also be used independently.

This is a discussion baseline, not proof of completed validation. The proposed development sequence may change.

Progress on 2026-10-17: M1 passed local alpha validation. The default became v2Pro with conservative punctuation hints; the user accepted a 72-second narration. The voice skill documents original/spoken text, retries and downstream handoffs. Native installation, other hardware and public release were still pending. M2 alignment was the recommended next module, starting with a plan and selection study.

Later M2 progress: the user accepted 72-second Chinese subtitle synchronization and removing cue-ending punctuation. Actual TTS frontend normalization, number/English mappings, standalone CLI and skill were connected. A 35.22-second mixed-language preview still awaited review. Storyboard-to-HTML/MP4 was next; this did not yet mean research, writing or full workflow support existed.

Later M3 progress: mixed-language subtitles were accepted. A maintainer prototype produced a 72-second, ten-scene HTML animation in portrait and landscape, with speech, captions and an avatar placeholder. Its 43 tests and full-video decoding passed; visual pacing awaited review. At that point video/scenes/storyboard skills and video setup were not yet packaged. Later updates below supersede these intermediate states.

## First-version scope

- Voice profiles: import reference audio/text and reuse a selected voice.
- Research: use online or supplied material; produce a beginner-friendly report with sources.
- Narration: adapt audience, style and requested length, with conversational Chinese editing.
- Speech: local segmented TTS, playback and targeted regeneration.
- Subtitles: align an accepted script to actual audio and export SRT.
- Video: combine dynamic visuals, user assets and a lower-right avatar placeholder into MP4.
- Tasks: retain intermediate artifacts, failures and production settings.

Potential extensions included batch topics, external asset retrieval, more aspect layouts, ASS captions and real avatar video. Voice training, fine-tuning and training-data management are outside the product and are not future tasks. Automatic posting, lip-sync avatars and a full editor are also outside the first version.

## Module boundaries

Research does not run TTS; writing does not synthesize; speech does not lay out captions; alignment does not rewrite facts or prose; video does not invent research conclusions. Orchestration connects modules and saves progress.

Storyboarding belongs to video and may start from a script, but exact durations come from generated audio.

## Milestones

| Stage | Work | Acceptance |
| --- | --- | --- |
| M0 Environment/selection | Confirm host, hardware and aspect; compare TTS; validate rendering | Local Chinese speech and a short rendered video, with speed, VRAM and issues recorded |
| M1 Voice | Profiles, segments, playback, retries | Reusable profiles; one retry preserves other audio |
| M2 Alignment | Forced alignment, cue splitting, export | Playable Chinese and mixed number/English checks; explicit anomalies |
| M3 Video | Storyboards, basic visuals, placeholder, rendering | Roughly one-minute synchronized sample; targeted visual changes can re-render |
| M4 Writing | Report extraction, spoken structure, editing, fact checks | Editable narration whose important claims trace to report sources |
| M5 Research | Search, extraction, evidence, report | Accessible writing, traceable sources, explicit gaps/conflicts |
| M6 Workflow/batch | Independent/combined entry points, reuse, recovery, task list | No overwritten outputs; resume from valid stages |

Deliver each module's independent interface, samples and instructions before integrating it. Use Python, structured files and necessary local processes; no HTTP interface.

## Acceptance approach

Use a few real Chinese examples covering concepts, mixed numbers/English, conflicting sources, speech retries, missing assets and interruptions. Naturalness, visual quality and synchronization require listening/viewing; successful commands alone are insufficient.

## Items to determine

1. Agent-plugin delivery is confirmed, prioritizing Codex, Claude Code and Cursor; native installation needs separate acceptance.
2. The inspected machine has Windows 10, RTX 3070 Ti 8GB and about 32GB RAM; recheck disk and dependencies before installing.
3. Target platform, aspect, video length and batch scale.
4. Commercial-use requirements and relevant model/dependency/media terms.
5. Initial voices, scripts, visual style and owned assets.
6. Permission for web research and any fully offline material mode.

## Decisions and subsequent updates

Confirmed: codoop-cast; independent modules; local first; document before implementing; topical visuals, captions, narration and avatar placeholder; GPT-SoVITS as the first engine. See the [voice plan](04-voice-implementation-plan.md).

At the initial voice milestone, pinned GPT-SoVITS/v2Pro passed reference-driven synthesis on Windows/NVIDIA and user listening review. Alignment, language-model choice, renderer, other hardware and batch throughput had not yet been validated. Local use without HTTP is confirmed; interaction and modules are separate. The script-to-video loop and explicit script/preview checkpoints were initial recommendations, not mandatory approval gates.

Subsequent 2026-10-17 updates:

- Storyboard/scenes/video skills, shared authoring/video setup and local commands were implemented: [video skills](18-video-skills-running.md).
- Research skill, report schema, evidence checks and export were implemented: [research](19-research-running.md). Writing was pending at that intermediate point.
- New content uses the [project layout](20-project-layout.md), explicit registered/current versions and dependency checks. External packages remain importable; shared models/environments stay outside projects.
- Writing skill, source identity, validation/export and storyboard import were implemented: [script](21-script-running.md). Voice paragraph identity was pending at that point.
- Structured `--script-file` speech, dual-text spans and original paragraph restoration were implemented: [script/audio adapter](22-script-audio-adapter.md), including alignment failures on pronunciation stress inputs.
- Single-project produce planning/state, version pinning and package assembly were integrated: [workflow](23-produce-running.md).
- Agent-driven sequential batch execution, failure isolation, pause/cancel, explicit recovery and versioned reports were integrated: [batch](24-batch-running.md), superseding earlier statements that batch was unavailable.
