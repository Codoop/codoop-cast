# Content project directories and filenames

[English](20-project-layout.md) | [简体中文](../zh-cn/20-project-layout.md)

Project format 0.1.0, introduced 2026-10-17. Apply to new projects; existing standalone packages remain imports without automatic moves. Seven skills shared it at that historical milestone. Installed execution guidance: `skills/codoop-cast-setup/references/project-layout.md`.

## Structure

One user-selected directory normally represents one topic/content item. Its display name can contain Chinese/spaces; managed internal names are fixed lowercase English/hyphens. Create only needed directories, not the entire empty tree.

```text
<selected-content-project>/
├── cast-project.json
├── research/v001/
│   ├── version.json
│   ├── report.json
│   ├── report.md
│   ├── checks.json
│   └── sources/<source-id>.md
├── script/v001/
│   ├── version.json
│   ├── script.json
│   ├── script.txt
│   └── script.md
├── storyboard/v001/
│   ├── version.json
│   ├── video-script.json
│   └── storyboard.md
├── assets/v001/
│   ├── version.json
│   ├── assets.json
│   └── files/<asset-id>.<ext>
├── voice/v001/
│   ├── version.json
│   ├── narration.wav
│   ├── narration.json
│   ├── original.txt
│   └── narration.txt
├── subtitles/v001/
│   ├── version.json
│   ├── subtitles.srt
│   ├── alignment.json
│   ├── audio.json
│   ├── script.json
│   ├── checks.json
│   ├── media/narration.wav
│   └── raw/
├── scenes/v001/
│   ├── version.json
│   ├── scene.json
│   └── files/index.html
├── exports/v001/
│   ├── version.json
│   ├── video.mp4
│   ├── production/
│   │   ├── package.json
│   │   ├── script.json
│   │   ├── video-script.json
│   │   ├── assets.json
│   │   ├── scene.json
│   │   ├── audio.json
│   │   ├── alignment.json
│   │   ├── timeline.json
│   │   ├── output-profile.json
│   │   └── <declared-media-HTML-audio-and-other-files>
│   └── video-qa/
│       ├── render.json
│       ├── ffmpeg.log
│       └── 01-<scene-id>.png
└── .cast/
    ├── work/<task-id>/
    ├── jobs/<task-id>.json
    └── locks/
```

Versions may include input snapshots required for standalone use, such as storyboard script/assets/profile/package files. Preserve upstream identities/revisions; copies are not freely editable duplicate prose. Declare auxiliary resources using package rules.

The script skill exists: [writing](21-script-running.md). Assets are now agent-managed: [assets](26-agent-assets.md). The tree above preserves the initial layout proposal; automatic asset build uses `media/<sha256>.<ext>` as specified in the later asset guide. `.cast/jobs` contains project task references as needed; real engine logs/models/Python/browser caches/cross-project voices stay in shared storage.

## Naming

- Root marker is cast-project.json, not project.json.
- Content hub is video-script.json, not plan.json/storyboard.json.
- Use voice, subtitles and exports, not new-project audio/alignment/renders aliases.
- Each stage versions independently: v001…v999, v1000. Never reuse/renumber; failed candidates can leave gaps.
- Core filenames omit topic/date/“final” suffixes already expressed by parent paths.
- Source notes use stable source IDs; media use stable asset IDs with real extensions. Extra explanatory files use descriptive lowercase/hyphenated names.
- Retain raw engine diagnostic formats/names to preserve refs. Screenshots use NN-scene-id.png; numbers extend beyond 99.
- UTF-8 content; relative slash-separated package paths, without developer paths/escapes. Existing engine manifests still include private paths, so full cross-machine replay is not claimed.

## Current versions/dependencies

cast-project.json holds identity/name/default profile/current. Each current stage is an explicit version or null. Do not infer acceptance from largest number/mtime.

`project register` writes version.json with stage/version, ready/partial, file hashes and exact upstream versions/manifest hashes. Directory versions and artifact revisions differ; a new run need not revise every input object.

Registered directories are immutable, including appended files. Make a new version for edits; omit old top-level version.json when copying a draft. Registration does not select. Select when the authorized task actually uses the result; do not add unnecessary approvals, and retain prior current while editorial review is pending.

| Status | Meaning |
| --- | --- |
| missing | No selected version |
| ready | Files/dependencies match registration, not factual/editorial approval |
| partial | Explicit incomplete result, such as research gaps |
| stale | Direct/indirect upstream selection changed |
| invalid | Missing/changed/extra files or changed dependency manifests |

Status only reports, never rebuilds/replaces/deletes. Registration checks structure/integrity, not each module's specialized validation.

## Agent commands

```text
project init --directory <project> --name <display-name>
project status --directory <project-or-child>
project path --directory <project> --stage research
research export --report-file <draft/report.json> --output <project/research/v001>
project register --directory <project> --stage research --version v001
project select --directory <project> --stage research --version v001
# Repeat --depends-on for actual upstream dependencies:
project register --directory <project> --stage script --version v001 --depends-on research=v001
```

Directory commands use stdlib without authoring/models. A candidate path is not a concurrent reservation; if occupied, request another path rather than overwrite. Mutable drafts/previews/assemblies use `.cast/work/<task-id>/`.

At the initial stage voice `--output` copied only WAV, so the agent also copied its returned manifest to narration.json plus original/narration text. Do not rename the engine manifest to standard audio.json; subtitle handoff creates the latter. Later structured export is described in the adapter guide.

Compile into exports/vNNN/production, render video.mp4 beside it; video-qa is generated automatically. Check before registering the whole export. Portrait/landscape get different export versions with precise profiles, not dimension suffixes.

Discover the nearest ancestor cast-project.json from the task directory. If none, initialize the selected content folder, never the plugin source because it happens to be cwd. Ask for location only if genuinely absent. Preserve imported packages and place new deliveries into new project versions.

## Implementation/validation

init/status/path/register/select are implemented; `project index --package` separately indexes package hashes. cast-project/stage-version schemas are included; folder management is stdlib-only.

Thirteen project tests covered idempotence/discovery/candidates/selection/transitive staleness/tampering/extra or missing files/nesting/version validity/overwrite/partial/moves. Seventy-three tests then passed: 50 ordinary/23 contracts. A real report exercised init/export/register/select/status. Other skill conventions were connected, but every media stage had not yet been regenerated under the new layout.

Subsequent 2026-10-17 updates: [structured speech](22-script-audio-adapter.md) preserves dual spans/original IDs and documents stress-input failures; [produce](23-produce-running.md) adds pinning/state/assembly; [batch](24-batch-running.md) adds sequential work, isolation, pause/cancel, explicit recovery and versioned reports, superseding older pending-batch notes.
