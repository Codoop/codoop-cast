---
name: codoop-subtitles
description: Generate local SRT subtitles and alignment timestamps from a completed codoop-cast narration or a local audio file with its transcript. Use for caption timing and subtitle export, independently of topic research or video rendering.
---

# Local subtitles

Before producing content, follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Resolve the plugin root two directories above the real location of this SKILL.md, following discovery links. Use the shared local launcher, not a server. Read [execution and artifacts](references/execution.md) for commands and limits.

1. Prefer the completed speech job explicitly selected by the user or unambiguously identified in this task. Otherwise accept local audio and a UTF-8 transcript; do not require using the voice skill first. Ask only for a missing or ambiguous input.
2. Run `doctor --feature alignment`; prepare missing dependencies through `codoop-setup`, then continue. Alignment has its own private environment; external audio does not require installing voice. Only Windows + NVIDIA is currently verified.
3. Run `subtitles generate` and inspect its exit status, checks, issues and warnings. The runtime uses selected audio, records actual TTS normalization for new speech jobs, and maps dates, prices and spelled letters back to display text. Do not guess a legacy recording's exact number pronunciation or hide missing mappings.
4. Return the SRT and structured artifacts; explain any unresolved timing issue briefly. Subtitle tails omit punctuation, while internal punctuation and meaningful symbols remain. Do not change the narration or original transcript to satisfy a visual preference.
5. When a preview is available, ask the user to judge synchronization and reading comfort. Successful alignment is not proof of correct pronunciation or absence of omitted words. Keep task ID and current audio/text versions for follow-up. Re-run after audio or transcript changes; do not reuse old timing silently.

Output includes script.json, audio.json with a local audio copy, alignment.json, checks.json and raw diagnostics. These are the handoff for scene timing and video composition; this skill does not write a storyboard, create illustrations or render a finished topic video. `needs_input` or no exported SRT is not success. Preserve earlier results when correcting a task.


## Content project

Before reading or writing task artifacts, follow the shared [project layout](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Use the user-selected content project, explicit current versions and canonical stage/file names. Keep shared environments and voice profiles in the configured data root. Existing external packages remain valid inputs; do not silently migrate them. Initialization-only setup does not require creating a content project.
