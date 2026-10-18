# Voice cloning: implementation and usage

[English](08-running-voice.md) | [简体中文](../zh-cn/08-running-voice.md)

Alpha implementation: setup/voice skills, shared local CLI, GPT-SoVITS v2 adapter, saved/reused voices, segment retries and automatic WAV joining. Code existence does not prove support for every host/device. See [validation](09-voice-validation.md).

## Entry point

Tell the agent, “Read this script using this voice.” Supply an original single-speaker recording; the plugin transcribes and selects a suitable reference locally, then saves it for reuse. Manual cropping/full transcription is unnecessary. Uncertain text is returned with its clip for confirmation. Identify the target in known multi-speaker material; automatic speaker separation is unavailable. Chinese and mixed Chinese/English narration are supported; training/fine-tuning are not.

Maintainer commands from the repository root:

```powershell
./scripts/cast.ps1 doctor --feature voice
./scripts/cast.ps1 setup --feature voice
./scripts/cast.ps1 voice create --audio 'D:/audio/original.m4a'
./scripts/cast.ps1 speech generate --text-file 'D:/scripts/narration.txt'
```

These are agent execution commands, not mandatory manual steps. Without Python, the Windows launcher downloads verified private uv/Python without changing global PATH. Existing Python 3.10+ can run `runtime/codoop-cast/cast.py` directly. For plain text, resolve the [current language policy](25-language-configuration.md) and pass `--language` when necessary.

Default storage: `%LOCALAPPDATA%/codoop-cast`. Use the same `CODOOP_CAST_HOME` for every child command to select another drive; this does not migrate existing data. The historical initial download estimate was approximately 2.3GB of models including recognition, plus CUDA PyTorch/dependencies/extraction/cache. Actual manifests and disk checks govern.

Arguments/rules: [voice execution reference](../../skills/codoop-cast-voice/references/execution.md).

## Distribution

Codex, Claude Code and Cursor manifests/marketplace files are present. Prefer native installation where verified, but published-repository commands need actual host testing; no store/native compatibility acceptance is implied.

Fallback:

```text
python scripts/install_skills.py --agent codex --dry-run
python scripts/install_skills.py --agent codex
```

`claude`/`cursor` are also targets. Copy the complete bundle and discovery links, without changing model storage. Windows symlinks require permission/developer mode; failure keeps the bundle and reports the problem. Native installation is an alternative where supported. Repeated execution refuses unrelated existing skills.

## Boundaries

- Only Windows/NVIDIA inference is implemented/verified here; AMD/Mac follow the compatibility plan.
- No HTTP/API/WebUI; initial dependencies/models require downloads.
- Inference enables Hugging Face offline mode. Real texts must expose implicit language/pronunciation downloads before claiming complete offline readiness.
- Cancellation occurs at paragraph boundaries, without immediate inference interruption guarantees.
- Segments/manifests/attempts are managed in private data, not by users.
- State is atomic JSON, not the initial SQLite proposal; add indexing only for demonstrated needs.
- Pronunciation, similarity and continuity require listening. Post-generation ASR QC is not implemented.
- Reference recognition uses local faster-whisper small CPU/int8; it differs from post-generation QC. Confidence helps transcript review and does not verify speaker identity.
- At this historical stage the code license was pending; see current root LICENSE/third-party notices rather than applying code terms to weights.

## Dependencies

Pinned GPT-SoVITS: `6df61f58e4d18d4c2ad9d1eddd6a1bd690034c23`, initially matching v2 synthesis weights. `runtime/codoop-cast/resources-voice.json` records URLs, versions, sizes and SHA-256. Download synthesis/base models, not discriminators/training-only resources.

To avoid requiring a Windows C compiler, adapt the upstream jieba_fast interface to pure-Python jieba. Retain upstream code/license in its private download; source is not copied into the release repository. Upstream imports such as Lightning do not expose a training product.

## Tests

```text
python -m unittest discover -s tests -v
```

These cover deterministic voice selection, CLI, paths, verification and joining. Model validation is recorded separately.

## Current default policy: 2026-10-17 update

New tasks use pretrained v2Pro without training. Setup verifies its weights/speaker encoder; old v2 resources remain for historical tasks. Upgrades perform real loading checks.

Store `original.txt` and `narration.txt`. Only selected commas/semicolons in longer Chinese sentences become full-stop hints; preserve every word. Short sentences remain unchanged. Split into at most 100-character chunks, infer each whole chunk, use 0.15-second model fragment interval and no extra 0.2-second export gap. Predicted pauses may still be unnatural.

Tasks pin model/policy for retries; historical tasks without these fields retain prior behavior. Targeted text retries preserve original input and update narration text. Each attempt records actual input/audio, and exports record selected text/model.
