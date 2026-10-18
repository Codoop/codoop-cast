---
name: codoop-script
description: Turn a research report or external report into natural spoken narration, preserving facts, uncertainty and available claim provenance. Use for voiceover writing or revising a narration before storyboarding and TTS.
---

# Narration writing

Before producing content, follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Use the [shared content project](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Read selected inputs from cast-project.json, write a new script/vNNN version and preserve earlier versions. Explicit external inputs remain supported; this skill does not require research, voice or video to have run.

Resolve the plugin root two directories above this SKILL.md's real location. Read [execution and handoff](references/execution.md) before creating artifacts. For prose editing use [spoken style](references/spoken-style.md); do not require a separately installed humanizer skill.

1. Read the actual report and user constraints. Prefer selected research/report.json and its pinned version; accept UTF-8 Markdown/plain reports independently. Infer audience and style from the task; resolve the artifact language through the shared configuration policy. If no duration was requested, write to the content rather than inventing a mandatory target. Do not repeat research automatically or present external report assertions as independently verified.
2. Choose the core explanation and necessary limits. Open with a concrete question or useful point, explain it in connected spoken prose and use an example when useful. Compression may omit peripheral claims, but cannot remove a condition that changes the central meaning. Avoid a fixed three-point template, fabricated personal experiences, false authority and dramatic promises.
3. Write script.json using the shared script schema. Preserve source report identity/revision or external source hash; map paragraphs to actual report claim_ids. Keep stable paragraph IDs across edits; generate new IDs on splits/merges and describe the relationship in provenance. Preserve numbers, dates, units, attribution, comparisons and uncertainty. An inference stays an inference; disputes and unsupported conclusions cannot become certain facts.
4. Keep display_text and spoken_text equal by default. Explicit pronunciation overrides may differ, but must preserve meaning and be checked. Retain natural punctuation for speech pauses. The subtitle-tail punctuation rule applies to exported captions, not to this narration. No final scene timestamps or caption timing are created here.
5. Review the prose aloud mentally, then compare it with the report for new claims or lost limits. Run script validate/export through the shared local launcher, using authoring setup only if missing. The local validator checks provenance and structure; it cannot prove wording is faithful or natural. Duration is a transparent character-count estimate, not a TTS measurement; revise text if its estimated length misses the requested target rather than claiming it fits exactly.
6. Deliver script.md for reading, script.txt for display/original text, script.json for structured handoff and spoken.txt for explicit spoken forms. Register the version with the actual research dependency, if present. Retain partial state when unresolved source gaps materially affect this narration. Show the real narration for review before downstream synthesis when it has not already been accepted; do not require a confirmation just to save/deliver the requested script.

This skill does not synthesize audio, design scenes or publish content. Existing context may authorize those separate tasks; completing this script alone does not imply they succeeded.
