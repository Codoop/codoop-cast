---
name: codoop-setup
description: Check, initialize, configure, or repair codoop-cast shared preferences and feature environments. Use for default artifact language, video production format, setup, or missing local dependencies, not general system maintenance.
---

# Shared plugin setup

Before producing content, read the shared [production settings](../codoop-setup/references/production-settings.md) for language, aspect, resolution, fps, captions and avatar configuration. Follow the shared [artifact language policy](../codoop-setup/references/language.md). Resolve the configured target language; the English instructions do not imply English deliverables.

Prepare only what the requested codoop-cast task needs. This is the shared initialization entry for all implemented features, not a GPT-SoVITS-specific product interface.

Resolve the plugin root two directories above the real location of this SKILL.md, following discovery links. Use `<plugin-root>/scripts/cast.ps1` on Windows or an available compatible Python to run `<plugin-root>/runtime/codoop-cast/cast.py`. Follow the versioned [shared data layout](references/data-layout.md) when initializing or repairing storage. Exact launcher and root conventions: [shared runtime](references/runtime.md).

1. Run `doctor` or `doctor --feature <feature>` without installing the feature. `voice`, `alignment`, `authoring` and `video` are registered. Storyboard/schema operations use lightweight authoring; HTML checks/MP4 export use video. Research and script validation/export use authoring; actual research uses the host agent tools and needs no additional model.
2. Infer the needed feature from the original task. If the user asks only for a check, report it without installing. For initialization, configure shared language and requested video preferences using the production-settings guide, preserving existing choices and using defaults for unspecified fields. Prepare feature dependencies only when the requested task needs them; no feature is required for configuration alone.
3. Reuse saved configuration and resource locations. First large setup: read `runtime/codoop-cast/resources-voice.json` for voice or `resources-alignment.json` for alignment, or resources-video.json for video; authoring has only schema dependencies. Sum asset sizes when no total is provided. Explain that additional private Python/PyTorch dependencies and extraction need more disk space, and state the target directory. Use an explicit data root if requested. Do not modify system Python, PATH, drivers, or unrelated tools. The bootstrap itself may download private uv/Python.
4. Run `setup --feature <feature>` within the user's authorized task and host permissions. Monitor stderr/logs. Initialization is idempotent and verifies pinned resources; repair missing components with the same command rather than upgrading packages ad hoc.
5. Report the actual state. If ready, return to the requesting skill and finish the user's task. If unsupported or failed, explain the actionable cause and retain successful resources. Do not repeatedly rerun a failing installation without investigating its log.

New features must register checks and preparation in the shared runtime and add only needed references. They reuse this skill rather than adding competing setup skills. No user audio is uploaded by these commands. Uninstall and moving an existing data root are not implemented; do not imply that changing an environment variable migrates stored voices.


## Content project

Before reading or writing task artifacts, follow the shared [project layout](../codoop-setup/references/project-layout.md), resolved from the installed skill's real path. Use the user-selected content project, explicit current versions and canonical stage/file names. Keep shared environments and voice profiles in the configured data root. Existing external packages remain valid inputs; do not silently migrate them. Initialization-only setup does not require creating a content project.

## Shared data and asset preparation

Explain the private data root only when relevant: it holds shared environments, downloaded models/tools, voice profiles and engine logs. It is separate from the installed plugin and portable content projects and is reused across projects. The default is the platform application-data directory; an explicitly configured `CODOOP_CAST_HOME` or `--root` can point elsewhere. Do not create a new root per project, silently migrate it, or remove it to fix a missing asset. Asset collection commands use the shared stdlib runtime without a new feature environment. Actual video media belongs in the content project, not the shared model directory. Image generation uses host capabilities only when available and needed.
