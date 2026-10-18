# Identity-preserving script, speech and subtitle adapter

[English](22-script-audio-adapter.md) | [简体中文](../zh-cn/22-script-audio-adapter.md)

> Historical implementation record. Current status: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

On 2026-10-17 `--script-file` allowed structured narration to reach speech, captions and scene timing without flattening it first.

## Actual flow

```text
script/vNNN/script.json
  → speech generate --script-file
  → voice/vNNN/narration.wav + narration.json + script.json
  → subtitles generate --job <speech-job-id>
  → original script.json + audio.json + alignment.json + subtitles.srt
  → compile original storyboard anchors against actual audio
```

Preserve artifact_id/revision, paragraph IDs, claims, source and dual text. Actual frontend-normalized text is separate, not a replacement script. Plain-text inputs retain legacy behavior; never infer missing original paragraph provenance afterward.

## Chunks and dual forms

Prepare each paragraph independently; split long paragraphs but do not join across them. The 100-character target is internal, not a whole-script limit. Pronunciation groups and atomic English/numbers stay intact, even if a chunk exceeds the target. Reference-recording import is unchanged.

Each chunk records:

- `script_spans`: Unicode-codepoint half-open ranges in original spoken_text.
- `display_span`: its original display_text range.
- `display_text`, `spoken_text`: original chunk dual forms.
- `text`: actual requested TTS input after conservative punctuation hints.
- `requested_mapping`: display to requested spoken form.
- `normalized_text`, `text_mapping`: observed actual frontend form and display mapping.

Numbers/punctuation use conservative mappings. Actual character substitutions need explicit `pronunciation_spans`, for example a homophone to guide a Chinese polyphone. The agent supplies display_start/end/spoken_start/end for agreed pronunciation; users need not calculate offsets. Reject unrelated undeclared rewrites, out-of-bounds/nonmonotonic spans; string similarity cannot prove pronunciation intent.

Grouped spans have group timing, not independent per-character precision. Valid indices do not prove that the reading/meaning is suitable; review remains necessary.

## Delivery/retries

```text
speech generate --script-file <script/vNNN/script.json> --voice <voice-id> --output <voice/vMMM/narration.wav>
subtitles generate --job <speech-job-id> --output <subtitles/vKKK>
speech retry --job <speech-job-id> --segment <one-based-index>
```

Structured export writes narration.wav/json, script.json, original.txt and narration.txt, refusing any target overwrite. narration.json remains an engine manifest with private chunk paths, not standard audio.json or a universally portable inference cache.

Structured retry can regenerate identical text but rejects `--text` replacement. Edit a script revision and create a new task for content changes so audio cannot silently diverge from planned scenes. Creation/resume/export verify pinned script fingerprints/chunk ranges.

Align within audio chunks, then remap to original paragraphs. The final script object equals the input. Audio spoken_text/script_spans reference requested original prose; optional normalized_text records actual frontend text, text_mapping relates local display to it, and display_span locates the chunk in its paragraph. Legacy artifacts need not add these fields.

Caption-tail punctuation removal remains display-only. Without reliable timing do not fabricate SRT.

## Local validation

- Twelve new checks covered long splitting/ranges, numbers, explicit homophones/grouping, ambiguous rewrite rejection, bounds, atomic groups, time remapping, script/chunk tampering, duplicate paragraphs, punctuation, export copies and pinned-text replacement rejection. Ninety-seven tests then passed: 62 ordinary/35 contracts.
- Actual source-linked three-paragraph script/v002 produced 43.73 seconds with the previously accepted voice, task `97a1c5b1f9fc45b8be9ac228cf15a5d8`.
- Subtitle task `874f52ac58a74cfba5e1f1285bd90e6a`, subtitles/v002: no issues/warnings; exact source script, paragraph IDs and claim refs retained. Three schemas, requested-text slicing and original-paragraph anchors for three scenes passed.
- voice/v001 and subtitles/v002 registered script/v002 dependencies without implying user listening acceptance from machine success.
- Extra stress input in `work/structured-audio-check` split one long paragraph into two chunks while retaining mappings. Explicit pronunciations/numbers mapped, but the aligner returned three terminal zero-duration units. Task `44b72b56ff234a0f89287c6c4f802aee` became needs_input, retained diagnostics and blocked SRT rather than inventing times.

Structural handoffs work, not every pronunciation/alignment. Listen/view for timbre, reading, omissions and sync. Full workflow/assets/batch were still pending at this historical stage; this run did not render another final video.
