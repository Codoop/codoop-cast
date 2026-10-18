# Subtitle skill and normalization mappings

[English](16-subtitles-running.md) | [简体中文](../zh-cn/16-subtitles-running.md)

On 2026-10-17 the standalone subtitle skill, shared alignment setup and CLI passed local Windows/NVIDIA alpha validation. At this stage it was unpublished; native hosts, all languages and hardware were not claimed validated.

## User entry

“Caption the previous narration” reuses a clearly selected completed task. External local audio/transcript also works without installing/using voice. Alignment has an isolated environment and no HTTP service.

```text
doctor --feature alignment
setup --feature alignment
subtitles generate --job <speech-job-id> --output <new-directory>
subtitles generate --audio <local-file> --text-file <utf8-transcript> --output <new-directory>
task status --job <subtitle-task-id>
```

Invoke via `scripts/cast.ps1` or compatible Python and `runtime/codoop-cast/cast.py`, with the same private data root. Use new destinations, never overwrite. Cancellation is checked between segments. Subtitle resume is not implemented; a new run preserves old tasks. Apply the current [language policy](25-language-configuration.md) for explicit transcript language.

## Actual speech and display text

Observe the frontend `preprocess` called during actual inference and retain `norm_text`. Do not parse debug logs, guess pronunciations or rerun preprocessing. Restore the original function on success/failure. Each attempt stores its own record; exports use only selected attempts.

Original text, requested TTS narration and internal normalized text are distinct. For example, `99.5元` can become `九十九点五元`, while captions retain the written number. Map numbers/dates atomically and keep contiguous ASCII tokens whole so CPU/GPU/SRT are not split into letter cues. Unreliably mapped rewrites fail explicitly rather than substituting unrelated text.

Numeric transforms support a defined set of spoken-number characters, not arbitrary aliases, unit replacements, special readings or mixed-case conversion. This is a conservative mapping, not a universal normalizer. Forced alignment cannot prove absence of omissions/mispronunciations.

Hide cue-ending punctuation; retain internal punctuation and meaningful symbols such as percentages. Display rules do not change timing. Preserve raw predictions when grouped-precision warnings occur; do not invent per-word durations.

## Outputs

- `script.json`: paragraph display text and normalized spoken form.
- `audio.json`, `media/narration.wav`: actual audio, chunk sample boundaries and spoken ranges.
- `alignment.json`: word/display-group times and cues, `span_basis=display_text`.
- `checks.json`: real audio SHA-256, engine version, coverage/anomalies.
- `subtitles.srt`, `raw-alignment.json`, `raw-units.json`: delivered captions and traceable evidence.

Artifact IDs derive from the subtitle task, with consistent references. Audio spans use spoken_text; displayed alignment spans use display_text. New output includes related audio so consumers need not infer paths or parse chat history.

This is an independently usable subtitle-package fragment, not all eight video artifacts. At this historical stage paragraphs derived from chunks; stable original paragraph IDs/many-to-many mapping still needed an adapter, without direct script.json input claims. See the later [adapter update](22-script-audio-adapter.md).

## Local validation

Normalized mixed-text speech task `a665971cbf574ebe9ac2590c3e10dc31` had the same WAV SHA-256 as the previous mixed-text run, showing observation did not change that audio. Mappings covered the date `2026年10月17日`, amount `99.5元`, CPU/GPU, 1080P and SRT.

Formal subtitle task `6c35d53b9087416495cc33e0555dfb90`: 35.22 seconds, 12 cues, no body-coverage/time-structure errors and two retained zero-duration grouping warnings. Numbers/English tokens remain whole. The first record awaited preview; the user subsequently viewed and accepted it. This acceptance does not cover arbitrary external inputs.

External-audio task `f0b2b3057f3444eb8585af609914e0c2`: 19.27 seconds of Chinese, successfully decoded/aligned/exported without voice setup.

Thirty-seven tests passed: 31 ordinary, six package contracts; setup/voice/subtitle skill validation passed. Repeated setup reused ready state. Before inference verify actual ranges, audio bytes and chunk manifest; equal duration is insufficient to accept replaced audio.

Fallback installation into an isolated Chinese/space agent-home passed; the copied CLI read alignment state. Delivered script/audio/alignment passed schema/reference/display coverage/trailing-punctuation checks. This is not native Codex/Claude/Cursor acceptance.

## Remaining limits

Legacy mixed-text speech without frontend records reports its limitation; resynthesize to capture real normalization instead of parsing logs. Legacy Chinese-only tasks may fall back to stored text.

External single-window audio is currently limited to five minutes. Automatic long-audio windows/text localization are not implemented: explain the capability gap rather than instructing manual cropping. For unknown numeric readings, accept a trustworthy `spoken-text-file`; otherwise alignment anomalies need review, without guaranteed recovery. Model load/SRT output alone does not prove synchronization.

At this stage AMD/Mac, clean user machines, native hosts, complex caption layouts, complete omission detection, HTML scenes and final posting videos were unaccepted. Subsequent structured speech/dual spans/original-ID restoration are described in the [adapter](22-script-audio-adapter.md), including pronunciation stress failures.
