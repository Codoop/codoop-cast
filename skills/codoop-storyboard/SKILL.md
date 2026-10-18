---
name: codoop-storyboard
description: Plan an editable video storyboard from a narration script. Use for semantic scene structure and visual event anchors, without requiring audio, a browser, or topic research.
---

# Storyboard

Before producing content, follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Resolve the plugin root two directories above the real location of this SKILL.md, following discovery links. Run `<plugin-root>/scripts/cast.ps1` on Windows (or a compatible Python with `<plugin-root>/runtime/codoop-cast/cast.py`). Global `--root` precedes the command; reuse the user's data root. Never hard-code maintainer paths. Read [execution](references/execution.md) and the applicable JSON schemas in `<plugin-root>/schemas/` before authoring artifacts. Agent performs structured edits; users should not need to edit JSON or install dependencies manually.

1. Accept an existing script artifact or the user's narration text; do not require earlier research skills. Use `storyboard prepare` in a new directory, preserving IDs/revision when importing script.json. Reuse an existing indexed authoring package when appropriate.
2. Read the topic and narration. Author video-script.json with scenes that explain the ideas, brief screen text, and a topic-specific visual intent. Choose scene count and visual language for this content. Preserve narration and facts; this skill does not rewrite the speech.
3. Use stable scene/event IDs, paragraph references and semantic anchors. Use display_text Unicode codepoint half-open ranges, not JavaScript UTF-16 offsets. Do not invent final durations or infer speech timing from word counts. Final timestamps come from real audio/alignment.
4. Plan stable semantic asset IDs and let `codoop-assets` prepare needed media automatically before scenes; do not ask the user to manage material files. Maintain the planning assets.json (empty is valid) and output-profile.json. Default portrait is only a starting preference; infer requested aspect, captions and avatar configuration from context. Keep artifact identity and increment revision on changes; update dependent references explicitly.
5. Run `project index`, then `storyboard validate`. Return a readable storyboard.md plus the structured package. For a standalone planning task deliver the actual scene plan for review. If the user has authorized a full draft-video workflow, continue within that scope while keeping editorial review distinct from machine checks. This is an independent completed plan, even before TTS exists.


## Content project

Before reading or writing task artifacts, follow the shared [project layout](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Use the user-selected content project, explicit current versions and canonical stage/file names. Keep shared environments and voice profiles in the configured data root. Existing external packages remain valid inputs; do not silently migrate them. Initialization-only setup does not require creating a content project.
