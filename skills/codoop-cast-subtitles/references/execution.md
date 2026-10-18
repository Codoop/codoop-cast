# Local execution and handoff

Use `<plugin-root>/scripts/cast.ps1` on Windows. Existing compatible Python can run `<plugin-root>/runtime/codoop-cast/cast.py`; global `--root` precedes the command. Follow setup's root conventions and reuse CODOOP_CAST_HOME. Do not hard-code maintainer paths.

```text
doctor --feature alignment
setup --feature alignment
subtitles generate --job <completed-speech-job-id> [--output <new-directory>]
subtitles generate --audio <local-file> --text-file <utf8-transcript> [--output <new-directory>]
task status --job <subtitle-task-id>
task cancel --job <subtitle-task-id>
```

Use an absolute UTF-8 file for long text; never interpolate its contents into shell code. The output option is a new directory, not a filename. Existing destinations are rejected. Run in the foreground using the host's long-process support; logs are under the private data root. Cancellation is checked between alignment segments. Resume is not implemented for subtitle tasks; a fresh generate preserves prior outputs.

For external audio, optional `--spoken-text-file` supplies a trusted exact spoken form separately from the displayed `--text-file`. This is not a requirement to manually transcribe or spell out numbers; use an existing reliable transcript when available. Unsupported or unreliable normalization returns a targeted problem rather than rewriting wording. External audio is currently limited by the tested single-window implementation to five minutes; automatic long-input windowing is not yet implemented. Report that capability limit instead of asking the user to cut audio manually or claiming long audio succeeded.

New voice tasks capture their actual synthesis frontend normalization. Historical Chinese-only tasks can align against stored text; legacy mixed-text tasks without that record require a new narration to obtain trustworthy normalization, unless another reliable spoken transcript exists. Do not parse debug logs into production transcripts.

`alignment.json` declares span_basis=display_text: text ranges are Unicode codepoint [start,end) positions in script paragraphs' display_text. audio.json spans refer to spoken_text; its text is the actual normalized input when recorded. Numbers and ASCII tokens are grouped for subtitle display; grouped units do not provide independent character timings. Original predictions, zero-duration grouping warnings and normalized mappings are retained.

`checks.json` includes selected audio SHA-256, model revision, coverage counts and issues. Ready means an SRT was exported; review_required remains true pending viewing. Text coverage is structural, not an ASR verification of the recording. Words omitted by TTS can still be forced onto timestamps; independent listening/content checks remain necessary. Plain SRT layout is a draft for later video styling.

The output directory is a self-contained subtitle handoff, not a complete video package. It includes media/narration.wav, script.json, audio.json, alignment.json, checks.json, raw diagnostics and subtitles.srt. Their artifact IDs match; exact video timing still needs storyboard anchors and HTML scenes. Changing display punctuation alone does not require resynthesizing audio or changing its timebase.


Structured speech jobs preserve their pinned script.json exactly, including artifact revision, paragraph IDs, claims and pronunciation overrides. Chunk-level alignment is projected back to each paragraph's original display_text ranges. audio.json's spoken_text/script_spans refer to the requested source spoken_text; optional normalized_text records the actual frontend form, and text_mapping maps display text to that form. Older plain-text tasks retain their legacy generated paragraph artifacts. Never overwrite a pre-existing planned script with a reconstructed chunk transcript when a structured source exists.
