# Open-source plugin and agent experience

[English](05-plugin-experience.md) | [简体中文](../zh-cn/05-plugin-experience.md)

> Historical design/validation record. Current status: [release readiness](29-release-readiness.md). First use: [installation](28-install-and-first-video.md).

This pre-release design corrects an early single-machine perspective: codoop-cast is an open-source plugin distributed to other users, with skills invoking local scripts rather than requiring an HTTP service.

## User journey

Install lightweight plugin → describe a task → agent checks readiness → prepare missing dependencies on first use → execute locally → return usable files.

Users need not learn Python, model startup or module calls. Download/setup costs are real; installation cannot imply instant synthesis on arbitrary hardware. The host must execute local processes and access selected files. Cloud-only agents without local access are outside the first version.

Scope follows content-making needs, not the upstream feature list. Voice covers reference reuse/narration, without training, fine-tuning or dataset management. Use a sole voice automatically; ask only when several are ambiguous. Technical settings are managed internally.

Example: “Read this with this voice” prepares the environment, selects/transcribes an original-recording clip locally, and returns WAV. Confirm text only when recognition is unreliable. “Use last time's voice” reuses it; “redo paragraph two” regenerates that passage.

## Skills

The early table below was later expanded by the [handoff contracts](13-skill-contracts.md): subtitles, storyboards, assets, HTML scenes and final composition are independent and exchange standard packages. At this historical stage setup/voice/subtitles had local alpha implementations; the rest were pending.

| Planned name | Intent | Necessary input |
| --- | --- | --- |
| codoop-setup | Shared checks, initialization, configuration, repair | Feature/data drive if needed |
| codoop-voice | Save profiles, synthesize, retry | Initial reference/text and narration |
| codoop-research | Research/report | Topic or supplied sources |
| codoop-script | Report to narration | Report; initial duration default proposal |
| codoop-video | Make video | Script or existing production artifacts |
| codoop-produce | Coordinate implemented capabilities | Topic or intermediate outputs |

Initially deliver setup/voice only; release other skills with working modules, not placeholders. Subtitles are explicitly independent and accept external audio/script; the newer contracts define their boundaries.

Setup is shared and feature-registered. Initially only voice was registered; future modules reuse it and prepare only missing task dependencies. See [setup design](07-setup-skill-plan.md).

Names/descriptions drive accurate discovery. SKILL.md holds essential flow/constraints; references hold details; scripts implement repeated operations. Automatic selection and explicit invocation depend on the host.

## Distribution

```text
codoop-cast/
  <Codex / Claude Code / Cursor manifests>
  skills/
    codoop-setup/SKILL.md
    codoop-voice/SKILL.md
  scripts/                    # local entry/bootstrap
  runtime/codoop-cast/         # shared CLI/modules/adapters
  docs/                       # maintainer documentation
```

This was a proposed layout, not a claim that this design stage created manifests/code. Skills guide agents; scripts perform deterministic checks/install/execution/recovery. Verify shared code ships and resolves: copying SKILL.md alone is not installation.

Like codoop-flow, thin host manifests wrap shared skills/runtime, with complete-copy fallback installation. Mark each host supported only after actual tests, not with invented universal commands: [compatibility](06-compatibility.md).

OpenAI provides [plugin packaging](https://developers.openai.com/plugins/build/plugins) and [skills](https://developers.openai.com/plugins/build/skills) specifications; skills do not inherently require MCP. Recheck the target host version before release.

## On-demand preparation

- Ship code/resource manifests, not large weights. Research/writing alone does not install GPT-SoVITS.
- Before first speech check OS, hardware, disk, dependencies and models; install missing pieces.
- Use private environments/compatible interpreters without uninstalling system Python or modifying global PATH. Removing 3.13 on the development machine was a personal request, not an installation step.
- Explain size/location before large downloads, using existing authorization/host permissions without redundant approvals or hidden necessary prompts.
- Pin dependency/model combinations and resource origins/hashes. Keep progress, resumable downloads and completion records; failed checks cannot report ready.
- Repair only private environments. Explain concrete driver/system issues requiring user action.
- Validate Windows/NVIDIA, then Windows/AMD, then Mac. Investigate and test the latter two before promising support; label CPU/Linux separately.

## Storage/lifecycle

Installed code is read-only/upgradable. Private environments, caches, voices and content use separate configurable storage, not plugin caches or the developer's E: path. Explicit settings precede platform defaults. Offer/retain another drive for first large setup. Upgrades preserve voices/content; uninstalling code does not delete projects. Treat caches, environments and personal data separately.

Initially run foreground commands whose worker reuses models within the task and releases VRAM afterward. A permanent daemon is unnecessary; optimize later for measured batch needs.

## Agent execution

Draft responsibilities: `doctor`, `setup --feature voice`, `voice create/list`, `speech generate/retry/export`, `task status`; packaging validation determines actual commands.

Return stable JSON with status, task ID, next action, error class and absolute output paths; diagnostics go to stderr/files. Long tasks persist state; agents wait/recover through host capabilities. Users should not search hidden folders for results.

Users choose reference, script, requested edits and destination; model paths/rates/splitting use tested defaults. Diagnose failures within bounds, asking only for necessary unresolved input.

## Release/acceptance

- At this design stage the project license was pending; require LICENSE/third-party notices and do not apply code terms to weights/fonts/media.
- Disclose download versus local-processing boundaries; do not upload voices/content by default or add undisclosed telemetry.
- Clean-machine cases: Chinese user names, space paths, non-admin accounts, repeat install, interruptions, upgrades and retained data.
- Verify skill discovery/CLI resolution without developer paths or undeclared global tools.
- Label actual tested hosts/platforms; do not advertise unimplemented features.
- A user obtaining an artifact through the agent is the acceptance criterion, not merely loading a model.

The first module therefore included setup/voice skills, CLI, on-demand installation and distribution checks; internal functions/protocols are not user requirements.

2026-10-17: [project layout](20-project-layout.md) added initialization, registration, explicit selection and dependency inspection. External packages remain valid; shared models/environments stay outside content projects.
