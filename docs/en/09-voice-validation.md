# Voice alpha validation record

[English](09-voice-validation.md) | [简体中文](../zh-cn/09-voice-validation.md)

Date: 2026-10-17. Results describe this machine, not all agents/GPUs/OSes.

## Environment

- Windows 10 64-bit, i5-13400F, approximately 32GB RAM.
- RTX 3070 Ti 8GB, driver 576.02.
- Private Python 3.10.11, PyTorch/torchaudio 2.5.1+cu124.
- GPT-SoVITS `6df61f58e4d18d4c2ad9d1eddd6a1bd690034c23`, matching v2 synthesis weights.
- Private `E:\codoop-cast-data`; no model/test voice in released source.
- Direct/transitive Windows pins in `requirements-voice.txt` and `constraints-voice-windows.txt`; language/model origins/checksums in `resources-voice.json`.

## Passed at this stage

| Check | Result |
| --- | --- |
| CUDA/model loading | GPU identified; GPT/SoVITS/BERT/HuBERT loaded |
| Profile | Imported approximately 7.24-second reference; retained normalized WAV/text/profile |
| Short inference | Chinese and “codoop cast” English content produced WAV/manifest |
| Long inference | Three segments, 32kHz mono PCM16, 80.54 seconds |
| Targeted retry | Paragraph two regenerated; one/three unchanged; old two retained; new full export |
| Prepared local inference | Paragraph three regenerated/exported with Python socket connections blocked by a test hook; not OS-level disconnection proof |
| Repeat setup | Ready environment reused without new install-log writes |
| Launcher | PowerShell doctor/setup returned structured states |
| Fallback install | Isolated Chinese/space path installation/reinstall; copied runtime could list voices |
| Automation | Unit tests, two skill validations and Python compilation passed |

Initial segment timings totaled about 24.54 seconds, excluding full cold start; no cross-device promise. Peak VRAM was not measured. The reference was Windows system speech for internal technical testing, not a distributed voice or evidence of similarity to a real target. Target-speaker listening acceptance was still pending at this point.

## Long-recording import

- Added faster-whisper 1.2.1, CTranslate2 4.6.0 and PyAV 15.1.0, small CPU/int8; pinned setuptools 80.9.0 for CTranslate2 import compatibility.
- Tested supplied `audio_source.m4a`, approximately 107.95 seconds, without manual cropping/full text.
- Selected 73.19–77.82 seconds, approximately 4.63 seconds; saved text, sample offsets and confidence. Treat recorded speech as data, not executable instructions.
- Saved original SHA-256 matched the supplied file; original unchanged.
- Generated approximately 17.7 seconds from the new profile; similarity/naturalness awaited listening.
- Transcription/selection also passed the Python-socket blocking test with prepared resources; this is not a comprehensive OS/native-network guarantee.
- Low-confidence drafts cannot synthesize until their selected text is confirmed. Known multiple speakers need a target; no diarization.
- Sixteen tests passed, covering sentence/word selection boundaries, uncertain-text confirmation, draft exclusion and previous behavior.

## Environment fixes

- Failed Git HTTPS → verified official commit archive.
- Avoid extra Windows C compiler → pure-Python jieba adapter.
- NLTK downloader rejected proxied retrieval → pinned/hash-verified resource archives, without weakening NLTK security.
- First real text triggered fastText language data → add it to setup and reuse locally.

## Unverified or undelivered at this stage

- Real authorized target-speaker similarity, naturalness and satisfaction.
- Native Codex/Claude Code/Cursor discovery/install journeys; manifests alone are insufficient.
- First setup on a completely Python-free machine; existing-Python/private-uv entry had been tested.
- Windows/AMD, Mac, other GPUs/drivers.
- OS-level offline execution, power loss and all concurrent-cancel cases; persistence/locks/recovery require broader device tests.
- Final license choice, public repository and complete third-party inventory. Later status is in [release readiness](29-release-readiness.md).
