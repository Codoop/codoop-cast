---
name: codoop-voice
description: Save and reuse a reference voice, generate local narration from a script, or redo part of a previous narration with GPT-SoVITS. Use for voice cloning and text-to-speech in codoop-cast.
---

# Reference voice and narration

Before producing content, follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Give the user an audio file from their reference voice and script. Do not expose model settings or ask them to perform installation steps. No training, fine-tuning, HTTP server, or WebUI.

Resolve the plugin root from the real location of this SKILL.md, following discovery links: two parent directories up. Shared entrypoint is `<plugin-root>/runtime/codoop-cast/cast.py`; do not resolve it from the current working directory. For Windows bootstrapping and exact CLI usage, read [local execution](references/execution.md).

1. Determine whether the user wants to save a voice, narrate text, or redo a previous segment. Accept script text, a UTF-8 file, or a structured script.json. Prefer speech generate --script-file for structured input to preserve paragraph identity and both text forms. Use a named existing voice when specified; if there is one voice, use it automatically; if several match, ask only for the missing choice.
2. For a new voice, accept the user's original single-speaker recording without asking them to cut it or type its transcript. `voice create --audio ...` performs local transcription and selects a bounded utterance for the backend. The original is preserved. A short clip with an exact user-provided transcript can bypass ASR. Do not reuse a long source's entire transcript for a selected excerpt. The filename is a sufficient default name. Never require training data.
3. Run `doctor --feature voice`. If setup is needed, follow the setup skill or read `../codoop-setup/SKILL.md`, prepare only voice, and continue the original request. Respect the host's permissions and existing authorization. Initial Windows NVIDIA support is the only implemented backend; do not claim AMD or Mac inference works.
4. Create the reference profile when needed, then generate narration. The default is pretrained v2Pro with conservative punctuation hints and automatic splitting. Jobs save original.txt and narration.txt separately; pause processing never adds or removes words. Do not rewrite wording without the user's agreement. Internal checks and WAV export happen automatically. Preserve the user's script; if a pronunciation needs correction, maintain the original and change only the agreed spoken form.
5. Present the resulting audio inline when possible, otherwise link its absolute local path. Offer the original and spoken text files when useful for review. A successful generation is not listening approval; use the user's feedback to decide whether pronunciation or pauses need a targeted redo. Keep job ID and voice selection available for follow-up; persisted task records permit recovery. Structured retries keep their pinned text; content changes require a revised script/new task. For “redo the second segment”, inspect task status first and use the one-based segment index; avoid guessing when the user's phrase is ambiguous.

CLI stdout is JSON; stderr is diagnostic output. A nonzero exit or failed state is not success. Read the relevant log, attempt only a targeted repair, and preserve successful audio. Do not invent transcripts, hide setup failures, or claim listening quality was verified solely because generation succeeded.

If import returns `needs_input`, present its selected clip and proposed transcript for confirmation/correction, then use `voice confirm`. Do not use an unconfirmed draft for generation. Speaker identity is not automatically verified: if the user says the source contains several people, clarify the intended speaker before import rather than claiming ASR separates speakers. Insufficient usable speech is a request for a clearer source, not a request for manual editing.


## Content project

Before reading or writing task artifacts, follow the shared [project layout](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Use the user-selected content project, explicit current versions and canonical stage/file names. Keep shared environments and voice profiles in the configured data root. Existing external packages remain valid inputs; do not silently migrate them. Initialization-only setup does not require creating a content project.
