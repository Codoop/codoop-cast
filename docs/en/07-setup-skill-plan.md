# Shared initialization skill design

[English](07-setup-skill-plan.md) | [简体中文](../zh-cn/07-setup-skill-plan.md)

Historical status: shared doctor/feature registration and voice setup had an alpha implementation; other registrations, configuration migration and cleanup were pending. The design below is plugin-wide, not a GPT-SoVITS installer or general system administration tool. See [readiness](29-release-readiness.md) for current capabilities.

## Responsibilities

Check this plugin's environment, configure shared storage/preferences, install feature dependencies/resources, verify versions, inspect state and perform bounded repair. Research, writing, subtitles and video integrate initialization here, while their own skills execute business work.

Users do not need internal feature IDs/commands. A skill declares requirements, setup prepares missing pieces, then returns to the original task. A standalone initialization request may inspect state and establish the intended released feature without downloading every model.

## Organization

- SKILL.md contains common flow, feature selection and handoff.
- References contain necessary feature-specific settings/troubleshooting, read only when relevant.
- Shared runtime implements doctor, configuration, verification and dispatch.
- Feature modules register preparation instead of putting all logic into skill prose or one giant script.

Initially register voice only; add research/script/alignment/video setup entries when implemented, not as placeholders. A valid outcome can be no additional installation, such as writing with existing host-agent capabilities.

## Feature initialization contract

Each entry declares ID, config version, supported platforms/backends, pinned dependencies/resources/checksums, prerequisites, readiness check and prepare/repair methods. Dependencies must be inspectable and acyclic.

1. Read settings and inspect requirements/hardware.
2. Compute the minimal missing scope, including necessary shared dependencies.
3. Explain downloads/location and genuinely missing input, using existing authorization/permissions.
4. Prepare missing pieces with progress/reuse/recovery.
5. Perform real readiness checks and retain versions/state.
6. Return structured results and continue the requesting task.

Results include feature ID, state, missing pieces, config references, necessary next actions and errors. Distinguish `ready`, `needs_setup`, `needs_input`, `unsupported`, `failed`. A check alone does not install; an authorized task/initialization may prepare requirements.

## Configuration boundaries

Shared settings hold the data root, caches and general preferences. Namespaced feature settings hold voice model/backend or video resources. Agents use stable commands; users need not edit files.

Changing one feature preserves others. Track shared-resource users so repair/update/cleanup cannot break active configurations. Conflicting backends use separate environments rather than one universal interpreter.

Task inputs, scripts, voices and finished media belong to business modules, not initialization preferences. Add credentials/accounts only if a future real feature needs them; do not request them preemptively or expose them in ordinary status.

## Acceptance

- Voice requests install voice requirements only, not research/video dependencies.
- Repeat/interrupted initialization reuses valid downloads and preserves preferences.
- A new feature adds its registration/implementation without rewriting other setup flows.
- One feature failure preserves ready ones.
- Shared-directory changes preserve settings; migration checks real files before updating references.
- Download completion without readiness checks is not success.
- Feature skills continue the original task. If nested skill invocation is unavailable, follow the same local scripts rather than assuming nonexistent tools.
