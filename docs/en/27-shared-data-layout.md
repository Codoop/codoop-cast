# Shared data directory convention

[English](27-shared-data-layout.md) | [简体中文](../zh-cn/27-shared-data-layout.md)

The agent/runtime manages private storage without manual directory creation. Windows defaults to `%LOCALAPPDATA%/codoop-cast`; this machine previously selected `E:/codoop-cast-data`. Precedence is global --root, CODOOP_CAST_HOME, then platform default. The root's name is flexible; its internal format is stable.

## Fixed structure: version 1

```text
codoop-cast-data/
├── data-layout.json                 # layout version and managed categories
├── config.json                      # shared preferences and feature settings
├── python/                          # private uv-managed Python
├── envs/
│   ├── voice/                       # GPT-SoVITS
│   ├── alignment/                   # forced alignment
│   ├── authoring/                   # structured editing/validation
│   └── video/                       # browser rendering
├── engines/
│   └── gpt-sovits/                  # pinned source/upstream-required resources
├── models/
│   ├── faster-whisper-small/
│   └── qwen3-forced-aligner-0.6b-hf/
├── tools/                           # uv.exe, ffmpeg.exe, shared executables
├── browsers/
│   └── video/                       # pinned Playwright browsers
├── features/
│   ├── voice.json
│   ├── alignment.json
│   ├── authoring.json
│   └── video.json                   # install/version/integrity state
├── voices/
│   └── <voice-id>/                  # 32 lowercase hex characters
│       ├── voice.json              # identity, text, language, resource paths
│       ├── original.<extension>     # reference recording copy
│       ├── reference.wav           # selected inference clip
│       ├── reference.json          # selection metadata
│       └── transcription.json      # when recognition ran
├── jobs/
│   └── <job-id>/                    # 32 lowercase hex characters
│       ├── job.json                # state, pinned input, actual outputs/errors
│       └── ...                     # task-specific inputs/chunks/alignment
├── logs/                           # setup/task logs
├── cache/
│   ├── downloads/                  # verified archives
│   ├── tmp/                        # child TEMP/TMP and temporary extraction
│   ├── uv/
│   ├── pip/
│   ├── huggingface/
│   └── nltk/                       # tool-managed caches
└── locks/                          # setup/GPU/config coordination
```

Create categories on demand, not empty directories/all models upfront. Preserve upstream filenames, environment layouts and browser version names. Models that GPT-SoVITS requires within its source tree stay there under manifest/integrity management, without duplicate copies in models.

## Naming/ownership

- Managed fixed names are lowercase ASCII, with hyphens for compounds.
- Environments/browsers/state use registered feature names. Reuse categories for new features rather than another root-level tree.
- Voices/tasks use stable IDs, not personal names/topics/mutable display labels.
- Adapters own task internals. Historical narration-id.wav/json, segment-id.wav and text files remain valid. Read actual job.json paths, never guessed names/directory order.
- Reports, scripts, assets, captions, scenes and videos live in project stage/vNNN. Shared jobs may retain engine outputs/handoff copies, not replace project deliverables.
- Do not store content projects in the shared root or commit private voices/models/logs.

## Lifecycle

Voices, jobs and config are persistent, not ordinary auto-deleted caches. Features contain installation proof, not manually editable ready claims. Caches are rebuildable but cannot be blindly cleared during work; no automatic cleanup command exists. Runtime releases locks; file existence does not establish safe deletion.

Python/environments/engines/models/tools/browsers can be reinstalled through shared setup/manifests. Do not delete the entire root to fix one feature or remove voices/tasks while reducing cache size.

## Compatibility/checks

Setup adds data-layout.json to existing roots, preserving resources, paths, unknown files and records. Doctor reports layout/registration/unmanaged entries read-only without migration/deletion. Unsupported future formats fail rather than being overwritten.

Changing --root/environment selects another location, not migration. Existing records may have absolute paths, so moving the directory is not guaranteed to work. Migration tooling is outside scope. The launcher uses explicit --root for both uv/Python bootstrap and runtime to avoid split storage.

The authoritative category list is `runtime/codoop-cast/castlib/data_layout.py`. New storage locations must update that declaration and this document rather than introduce unowned root folders.
