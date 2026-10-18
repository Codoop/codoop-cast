# Subtitle and alignment module

[English](alignment.md) | [简体中文](../../zh-cn/modules/alignment.md)

Historical plan: [implementation plan](../12-alignment-implementation-plan.md), with Qwen3-ForcedAligner first and WhisperX as fallback before a default was installed/pinned. Current implementation is described in [subtitle usage](../16-subtitles-running.md).

## Inputs/outputs

Input: final/segmented audio, corresponding spoken text, display mapping and layout settings. Output: word times, paragraph boundaries, cues, SRT and anomalies; ASS could follow. Accept external audio/transcripts independently.

## Flow

1. Check audio/text correspondence; route obvious omissions/repeats back to speech.
2. Resample copies for the model, retaining original audio as timebase.
3. Force-align known spoken text to actual speech.
4. Restore readable display numbers/punctuation/acronyms through mappings.
5. Form cues using semantics, length, dwell and aspect.
6. Add segment offsets and export full-track captions/checks.

## Timing/display

- Hide cue-ending punctuation while retaining internal punctuation/meaningful percentages. This does not edit script, speech or timing.
- Do not allocate duration by character count or overwrite scripts with unchecked ASR.
- Times are ordered/in bounds; initial ordinary captions do not overlap.
- Reject negative/zero-length cues and large bodies flashing too briefly.
- If no model confidence exists, flag bad ranges/gaps/mappings with rules, not invented scores.
- Check wrapping with actual fonts/aspect, not only a character limit.
- Alignment success does not prove pronunciation; keep listening/QC available.

Acceptance covers Chinese/numbers/English, pauses and joins; loadable SRT, boundary sync checks and invalidation after audio changes.
