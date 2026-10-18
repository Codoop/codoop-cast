# Subtitle and alignment implementation plan

[English](12-alignment-implementation-plan.md) | [简体中文](../zh-cn/12-alignment-implementation-plan.md)

> Historical record. Current capabilities/gaps: [release readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

Baseline on 2026-10-17: no aligner installed/validated. Validate before pinning a default, independently of accepted speech. A later isolated native-Transformers Qwen experiment produced a Chinese 72-second SRT/preview; mixed text failed and setup/skill were not yet registered: [experiment](15-alignment-validation.md). Subsequent normalization mappings, standalone skill/setup/CLI are described in [subtitle usage](16-subtitles-running.md).

## Experience and scope

The proposed independent `codoop-subtitles` accepts “caption the previous narration” or local audio/transcript. Prepare dependencies, align, split and export SRT without model selection, timecodes or manual segmentation.

Start with known-script, single-speaker Chinese narration, numbers and some English. Audio without a transcript has missing input; arbitrary transcription is not mandatory here. No HTTP, training, diarization, translation, karaoke highlighting or ASS editor.

## Candidates

| Candidate | Relevance | Validation | Decision at baseline |
| --- | --- | --- | --- |
| Qwen3-ForcedAligner-0.6B | Official independent audio/text-to-word align interface | Windows, 8GB VRAM, attention implementation, mixed text mapping | First local experiment, not yet pinned |
| WhisperX + Chinese model | Existing Chinese alignment adapter/known intervals | Vocabulary, numbers/English, missing timestamps, dependency size | First fallback |
| FunASR timestamp tools | Timestamp capabilities vary by model/entry | Verify actual known-script alignment rather than transcription timestamps | Lower priority |

Upstream describes 11 languages including Chinese and up to five-minute inputs. This is not a reason to make users crop files. Prefer real plugin speech chunks; long external audio needs automatic windows and text localization, not copying the entire script to each window. If unvalidated, explicitly limit support.

Use isolated `envs/alignment`, not assumed compatibility with voice dependencies. Prefer native Transformers and an attention implementation needing no compilation; vLLM/FlashAttention are not prerequisites. Pin private Python after tests; leave system Python alone. Run after the speech worker exits to avoid simultaneous VRAM use.

After real tests, pin versions, model revision/hashes, download size, constraints and code/model terms. Upstream README support is not project validation.

## Flow

1. Accept a speech task or audio + UTF-8 transcript. Task mode reads current selected audio/chunks/actual speech text.
2. Retain hashes and origin; decode/resample copies without changing originals.
3. Map display text, actual spoken text and alignment units. Flag unreliable numbers/units/acronyms; never discard characters to claim coverage.
4. Align plugin chunks and restore full-track sample offsets. Use validated windows for unsegmented external inputs.
5. Check coverage, monotonicity, bounds, zero durations, anomalous silence and possible omissions. Forced alignment does not prove every word was spoken; content checks/anomalies remain necessary.
6. Form cues using punctuation, semantics, reading length and dwell time. Initial short lines use adjustable conservative rules, not claimed font-layout validation.
7. Export UTF-8 SRT, structured times and checks. Temporary subtitle previews are allowed; final rendering belongs to video.

## Artifacts/recovery

Each task retains input digests, engine version, raw predictions, mappings, cues, anomalies and exports in its own directory. Reuse existing structured statuses such as ready/needs_input/failed and valid segments.

Primary outputs: `subtitles.srt`, `alignment.json`, `checks.json`. Use original-audio samples/rate throughout; convert to milliseconds only for SRT and recheck positive, nonoverlapping, bounded cues after rounding. Display/spoken forms need explicit mapping, not proportional timing from character counts.

Reuse identity includes actual selected audio hash, current segment/display text, engine/weight versions and caption settings. Changed speech/scripts invalidate captions; the original input file may not describe current selected speech.

## Proposed plugin interfaces

Register `doctor --feature alignment` / `setup --feature alignment` in shared setup, not a subtitle-specific setup skill. Proposed generation: `subtitles generate --job <speech-job-id>` or `--audio <file> --text-file <file>`, returning task ID/artifacts. Local files only. Resolve clear recent inputs and ask only for ambiguity. Do not advertise alignment before registration.

## Implementation/acceptance sequence

1. Test the accepted 72-second audio in an isolated environment; record installation cost, runtime, RAM/VRAM and coverage.
2. Test Chinese, numbers/dates/currency, acronyms, long pauses, intentional omissions and retries; returned results/zero exit codes are insufficient.
3. Pin a passing candidate and integrate setup, CLI, task reuse, mappings and SRT.
4. Add the skill and validate packaged paths; native installation remains separate.

Machine checks reject negative/out-of-range/reversed/illegal overlaps, silently missing meaningful text, reused stale results and overwrites; failures identify affected ranges.

Listen/view at the beginning, middle, end and at least two pauses of the 72-second sample. Approximately 200 ms boundary error is a target, not a measured result. Numbers/English need separate review. Complete this before minute-long video composition.

## Primary references

- [Qwen3-ASR/ForcedAligner](https://github.com/QwenLM/Qwen3-ASR): interface, languages, length and environment guidance.
- [WhisperX](https://github.com/m-bain/whisperX), [alignment source](https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py): Chinese models/structure.
- [FunASR](https://github.com/modelscope/FunASR): inspect specific model/task; ASR timestamps are not necessarily forced alignment.
