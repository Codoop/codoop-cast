# Local alignment validation

[English](15-alignment-validation.md) | [简体中文](../zh-cn/15-alignment-validation.md)

> Historical experiment. Current status: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

On 2026-10-17 the prototype aligned Chinese successfully, but mixed number/English input failed. The subtitle skill, shared setup and formal CLI were not yet connected. Subsequent actual frontend records/group mappings and packaging are described in [subtitle usage](16-subtitles-running.md); retain this record as experimental history.

## Environment/selection

Windows 10 / RTX 3070 Ti 8GB, private `envs/alignment`, Python 3.10.11, torch/torchaudio 2.5.1+cu124, Transformers 5.13.0, accelerate 1.12.0, native AutoModelForTokenClassification, CUDA float16/SDPA. No FlashAttention, vLLM or qwen-asr demo-service dependencies; voice environment unchanged.

Official `Qwen/Qwen3-ForcedAligner-0.6B-hf`, revision `c07281df297b9905d24a508279258cccf987a064`, weight SHA-256 `00568245ceca5af1991d28562a75fe1ddc9bfeb041c27fda66947ea05c47fb86`. `resources-alignment-experiment.json` records resources/hashes, rechecked before runs. The card stated Apache-2.0; the project license was then pending, without conclusions about all dependencies.

Native Transformers reduced unrelated UI/multilingual-tokenization dependencies. It does not prove the older qwen-asr package incompatible with Windows: only parsing, not actual installation, had been checked.

## 72-second sample

Use accepted task `127329545b5b4af4a0ca205b4f47ae91` and its four selected chunks. Restore actual original sample offsets; resample copies to 16k only. Final audio remains 32k, 2,304,000 samples, 72 seconds.

Initial output had 279 body units and three zero-duration characters, blocking export. Later grouping was allowed only for adjacent text in the same segment, a positive-duration neighbor and a gap ≤160 ms. Preserve raw-alignment.json/raw-units.json/warnings. Group times do not establish separate character precision. Do not invent duration or merge across clear pauses. Upstream decoding already performs monotonic repairs; retain raw class IDs too.

Final alignment-03: 276 units, 26 cues, all 279 nonpunctuation body characters covered, without reversed/out-of-range/illegal-overlap/zero-duration units. Millisecond rounding passed. Three grouped-precision warnings remain and state is needs_review. Jieba assists word boundaries/short-cue merging; viewing still judges splitting.

Measured loading ~1.52 s, four forward/decode passes ~0.70 s, recorded process ~2.81 s including loading/grouping but excluding interpreter/imports/hash checks/downloads. CUDA peak allocated 2,074,262,016 bytes, reserved 2,359,296,000 bytes. These timings apply only here.

`subtitle-preview.mp4` uses solid background, original narration and burned captions at 720×1280/30fps. It is a sync preview, not a topical posting video. The eighth-second frame confirmed fonts/bounds. Initial beginning/middle/end listening had not yet established the 200 ms target.

Actual audio/alignment were copied into an output package with updated revisions/references/hashes and passed cross-file validation. HTML was unbuilt and timeline blocked. Public examples remained pending without personal audio.

## Mixed sample/failures

The user later accepted the 72-second timing and requested no punctuation at cue ends. Display rules remove trailing punctuation, retain internal punctuation/meaningful symbols and leave audio/alignment unchanged. This accepted the Chinese sample, not unresolved mixed input.

Task `cf22280eea8941e3a1f57fe884d5707e`: 35.22 seconds with date, 99.5 currency amount, CPU/GPU, 1080P and SRT. Body tokens covered 114 characters, but 1080P had zero duration without a permissible neighbor merge, so no SRT; another cue was only ~400 ms.

Frontend diagnostics showed actual Chinese readings: date “二零二六年十月十七日”, 99.5 as “九十九点五”, split acronym letters, and 1080P as “幺零八零P”. Display input alone cannot guarantee alignment. The stored pre-TTS narration did not yet include complete frontend output: a real handoff gap.

Next: observe actual normalized text, map display groups to speech and retest. Do not guess numbers, skip words or loosen checks to claim success. External audio, long windows, omission detection and final aspect-specific caption layouts were unverified.

## Implementation/checks

`scripts/align_experiment.py` accepts local task/model/new output directories, loads offline paths and starts no HTTP. Experiment constraints/dependencies were outside generic setup; no general install entry existed yet.

Twenty-two runtime/reference/alignment-helper and six package-contract tests passed, plus real Chinese/mixed experiments. Checks include unmapped-text rejection, numeric/punctuation ranges, retained raw zero-duration grouping and no merging across clear pauses.

Sources: [model card](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B-hf), [pinned processor](https://github.com/huggingface/transformers/blob/v5.13.0/src/transformers/models/qwen3_asr/processing_qwen3_asr.py). Model/library source unchanged.
