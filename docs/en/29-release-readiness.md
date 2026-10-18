# Alpha release readiness

[English](29-release-readiness.md) | [简体中文](../zh-cn/29-release-readiness.md)

Updated 2026-10-18. This is the current release-status entry. Earlier plans/experiments retain historical facts; their “unimplemented” statements do not define today's capabilities.

## Available

- Ten English-instruction skills: setup, research, script, voice, subtitles, storyboard, assets, scenes, video, produce.
- Local Chinese reference voice/speech, actual-audio alignment, punctuation-free cue tails, HTML animation to portrait/landscape MP4. No voice training.
- Structured reports, source-linked scripts, stable paragraphs, dual display/spoken forms, versioned outputs.
- Single-project recovery, agent-driven sequential batches, automatic media/provenance and visual-only rebuild scope.
- Shared/project language settings, data-layout version marker and on-demand private environments.
- Complete-copy fallback/isolated Chinese-space-path checks, distinct from native-host/clean-machine acceptance.

## Release checklist

| Item | State | Evidence needed |
| --- | --- | --- |
| Project license | Apache-2.0 selected | Root LICENSE/NOTICE/THIRD_PARTY.md added |
| Third-party software/models/fonts/media | Consolidated review pending | Inspect actual pinned resources; code terms do not relicense weights |
| Native Codex/Claude Code/Cursor | Per-host acceptance pending | Versions, installation, discovery, real commands |
| Clean Windows/NVIDIA | End-to-end acceptance pending | Non-admin, Chinese/space paths, initial download/repeat setup/first MP4 |
| Upgrade/interruption | Local tests exist; clean-machine extension pending | Retained voices/projects and actual long-task recovery |
| Fresh-topic batch videos | Content-quality acceptance pending | Multiple fresh topic-to-video runs, failure isolation, asset edits |

AMD/macOS/English listening are subsequent validation, not supported claims. They need not block a clearly scoped Windows/NVIDIA alpha for testers. No automatic posting, lip sync, full editor or automatic data migration/cleanup.

## Packaging boundaries

Ship complete skills/runtime/scripts/schemas and necessary manifests, plus documentation/examples as appropriate. Exclude work, personal recordings, shared data, caches, Python environments, weights and task logs. Inspect actual release content first; this preparation does not automatically commit/push/publish or change the chosen license.

Separate structural tests, real inference/rendering and human review in reports. Counts do not replace host/clean-machine evidence. Maintainer test entries:

```text
python -m unittest discover -s tests
<authoring-python> -m unittest discover -s tests/contracts
```

Authoring-python is setup's private environment with pinned jsonschema. Users should not install global development dependencies just to use the plugin.
