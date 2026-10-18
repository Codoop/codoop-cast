# Timbre improvement: same-script comparison

[English](10-voice-comparison.md) | [简体中文](../zh-cn/10-voice-comparison.md)

Historical status: first local comparison complete, user preference pending; defaults/profiles unchanged. No training or additional user settings.

## Method

Same short script, speed 1.0, seed 42 and sampling settings. A/B compare reference clips; A/C/D compare matching pretrained model combinations. Pro models need matching semantic weights/speaker encoders, not just one acoustic weight change.

| Sample | Model | Reference | Output duration |
| --- | --- | --- | --- |
| A | v2 | Original selected approximately 4.63 s | 17.70 s |
| B | v2 | Another approximately 7.59 s from same recording | 20.38 s |
| C | v2Pro | Same as A | 16.34 s |
| D | v2ProPlus | Same as A | 16.34 s |

A/C/D keep the main reference identical. B deliberately changes length/location; it does not establish that longer is better. All four files are valid/nonempty and have distinct content hashes.

Listening copies use basic RMS matching with peak limiting, preserving pitch/speed and raw outputs. RMS is not perceptual loudness or similarity scoring.

Compare timbre, speaking habits, pronunciation and naturalness. Successful code, bigger models or names do not prove target similarity; listening is necessary.

## Implementation/resources

`scripts/compare_voice.py` uses the private voice environment and separate outputs without changing profiles/production settings. `runtime/codoop-cast/resources-voice-comparison.json` pins optional weights, sizes and hashes outside ordinary setup's mandatory downloads.

v2Pro/v2ProPlus loaded and synthesized on RTX 3070 Ti 8GB. The adapter checks the version actually recognized upstream to prevent loading new files under old-mode behavior. Upstream source is unchanged; model selection was an experiment, not a public CLI setting.

Sixteen automated tests and actual A/B/C/D synthesis passed for v2/Pro branches. Other GPUs, native installation and cross-machine reproduction remained untested.
