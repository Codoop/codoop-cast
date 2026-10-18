# Voice and speech module

[English](voice.md) | [简体中文](../../zh-cn/modules/voice.md)

First engine: GPT-SoVITS. Alpha model loading, reference synthesis and retries ran on Windows/NVIDIA. See [usage](../08-running-voice.md) and [plan](../04-voice-implementation-plan.md).

## I/O

Profile input: an owned/authorized original recording, optional name. Output: reusable voice. Select/transcribe automatically; confirm only unreliable text. Accurate optional short-reference text can bypass recognition. Model/settings are managed internally.

Speech input: text/script and profile. Automatically use the only profile; ask when multiple are ambiguous. Output: playable/exportable WAV. Retain segments/manifests/checks for downstream work; no report prerequisite.

## Approach

Reference-driven cloning retains reusable reference conditions only. Training, fine-tuning and dataset management have no skill, command, UI or roadmap here.

The engine adapter checks readiness/references and synthesizes only necessary operations. Map natural-language speed requests to validated settings rather than exposing the upstream toolkit.

## Flow

1. Validate local audio; transcribe and select sentence/word-timestamp clips, preserving originals/offsets. No automatic identity recognition; clarify known multi-speaker targets.
2. Normalize number/unit/acronym/polyphone readings.
3. Synthesize semantic passages under fixed reference/settings.
4. Check files/silence/duration anomalies; ASR can assist omission/repetition review.
5. Allow playback and bounded retries.
6. Normalize/join audio/pauses and retain exact sample boundaries.

ASR differences may be recognition errors, not proof TTS is right/wrong. Listen for cross-segment timbre/tone.

## Resources/recovery

Schedule GPU stages within resource limits and support explicit model unloading. Validate prepared inference offline; do not assume dependencies never download implicitly.

Record engine/weights, supported seed/settings, input hashes and profile version for traceability, without sample-identical cross-hardware promises.

Acceptance: reusable profile, Chinese/mixed numeric listening samples, failures preserving successes, and intermediate audio independently consumable by alignment.
