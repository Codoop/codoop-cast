# Pause comparison experiment

[English](11-pause-comparison.md) | [简体中文](../zh-cn/11-pause-comparison.md)

On 2026-10-17 the user preferred v2Pro/v2ProPlus timbre slightly but reported pause problems. Continue with the same profile/reference, v2Pro, seed 42 and speed 1.0, initially without changing production defaults.

Maintainer script: `scripts/compare_pauses.py`, an experiment rather than a user skill/installer. Its original local-data paths were subsequently replaced with explicit `--root` and `--comparison-file` arguments.

| Sample | Treatment | Duration |
| --- | --- | --- |
| E | Whole original text, 0.3 s fragment interval | 16.34 s |
| F | Whole original text, 0.01 s interval | 16.05 s |
| G | Split at Chinese full stops, sequential inference, 0.15 s interval | 22.29 s |
| H | Last sentence rewritten as two complete sentences, whole-text inference, 0.15 s interval | 18.51 s |

E/F isolate the interval parameter: long internal silences stayed at the same positions, with mainly 0.29 seconds removed from the end. Lowering it does not solve this sample's internal pauses; do not generalize beyond this whole-text sample.

G changes splitting and parallelization together, so cannot isolate one cause. H changes phrasing and adds the Chinese pronoun “你”; preserve the original and obtain the user's preference before adopting edits. Do not rewrite the script by default.

An earlier all-punctuation/parallel experiment generated only 5.8 seconds for approximately 80 Chinese characters, indicating a serious anomaly. It was excluded, retained for diagnosis, and not promoted as valid faster output.

Listening files were in `outputs/voice-pauses-03`; raw files retained, `*-listen.wav` RMS-matched only. Silence scans use 10 ms windows/RMS 0.003, a diagnostic rather than word alignment or proof of naturalness. Local faster-whisper assists content checks; it cannot replace listening.

ASR did not fully recognize E/F's opening Chinese phrase “复制效果测试。以后只”; unclear generation, omission or recognition error needed listening. G/H largely covered the full content, with recognition confusions such as “裁切/彩切” and “生成/生存”. ASR differences are not definitive model-omission findings.

These outputs bypassed the plugin's extra 0.2-second join gap, which required a separate long-script test. Initially keep production splitting/text/model/interval unchanged until preference and effective strategy are established.

## Production integration after choosing H

The user selected H and authorized integration. New tasks use v2Pro, 0.15-second fragment interval and whole-chunk inference, with at most 100-character chunks rather than splitting every comma. Chinese semicolons/selected long-sentence commas become full stops. Preserve every nonpunctuation character; do not copy H's added pronoun. This conservative deterministic approximation is not semantic rewriting or a promise of identical pacing.

Tasks retain original/spoken text, model and policy. New exports add no join gap; historical tasks keep their prior model/fallback interval. v2 resources remain; setup prepares and actually loads Pro weights/encoder.

The user subsequently accepted a 72-second production narration. That applies to this sample/machine only. The next independent module was alignment/subtitles.

The formal CLI also produced a 304-character, four-chunk script: task `127329545b5b4af4a0ca205b4f47ae91`, 72.00 seconds, manifest samples matching WAV and continuous boundaries. Small ASR covered the content without obvious missing chunks, not replacing listening. Output: `voice-h-long.wav`, original/spoken texts and transcription checks. Eighteen tests and voice-skill validation passed; the intermediate run record still awaited the long-sample listening later noted above.
