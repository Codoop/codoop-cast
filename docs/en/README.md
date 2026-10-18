# Documentation

[English](../en/README.md) | [简体中文](../zh-cn/README.md)

User and maintainer documents are paired across en and zh-cn. Skill instructions and references remain English only. Historical documents retain their original stage-specific status; use release readiness for current capabilities.

## Documents

- [Overall plan](01-plan.md)
- [Technology selection](02-technology.md)
- [Workflow and data conventions](03-workflow.md)
- [Voice cloning and speech skill implementation plan](04-voice-implementation-plan.md)
- [Open-source plugin and agent experience](05-plugin-experience.md)
- [Agent and hardware compatibility plan](06-compatibility.md)
- [Shared initialization skill design](07-setup-skill-plan.md)
- [Voice cloning: implementation and usage](08-running-voice.md)
- [Voice alpha validation record](09-voice-validation.md)
- [Timbre improvement: same-script comparison](10-voice-comparison.md)
- [Pause comparison experiment](11-pause-comparison.md)
- [Subtitle and alignment implementation plan](12-alignment-implementation-plan.md)
- [Independent skills and workflow handoff contracts](13-skill-contracts.md)
- [Minimal production package v0.1.0](14-production-schema.md)
- [Local alignment validation](15-alignment-validation.md)
- [Subtitle skill and normalization mappings](16-subtitles-running.md)
- [First HTML animation video sample](17-html-video-validation.md)
- [Video skills usage](18-video-skills-running.md)
- [Topic research usage](19-research-running.md)
- [Content project directories and filenames](20-project-layout.md)
- [Narration-writing skill usage](21-script-running.md)
- [Identity-preserving script, speech and subtitle adapter](22-script-audio-adapter.md)
- [Single-project workflow skill usage](23-produce-running.md)
- [Batch queue usage](24-batch-running.md)
- [English skills and configurable artifact language](25-language-configuration.md)
- [Agent-managed assets](26-agent-assets.md)
- [Shared data directory convention](27-shared-data-layout.md)
- [Installation and first video](28-install-and-first-video.md)
- [Alpha release readiness](29-release-readiness.md)
- [Subtitle and alignment module](modules/alignment.md)
- [Topic research module](modules/research.md)
- [Narration writing module](modules/script.md)
- [Video production module](modules/video.md)
- [Voice and speech module](modules/voice.md)
- [codoop-cast v0.1.0-alpha.1](releases/v0.1.0-alpha.1.md)

## Maintenance

Update both editions in the same change, preserving commands, IDs, hashes, dates and verification limits. Do not translate LICENSE/NOTICE, schema keys or fixed artifact filenames. Evidence fixtures remain canonical and receive separate English reading editions rather than changed hash-pinned source text. Validate with `python scripts/check_docs.py` from the repository root.
