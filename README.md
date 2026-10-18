# codoop-cast

[English](README.md) | [简体中文](README.zh-cn.md)

A local-first agent plugin for narrated social-media knowledge videos. Research a topic, write narration, clone a reference voice, align captions and create animated HTML visuals/MP4. Use capabilities independently or combine them into sequential batches.

Current version: [v0.1.0-alpha.2](docs/en/releases/v0.1.0-alpha.2.md) (pre-release).

Current stage: alpha implementation and local validation. Ten skills cover setup, research, script, voice, subtitles, storyboard, assets, scenes, video and produce. Native host installation and additional hardware require separate acceptance; see [release readiness](docs/en/29-release-readiness.md).

Default speech uses pretrained GPT-SoVITS v2Pro with conservative punctuation-based pause hints. Tasks retain original/spoken forms; new exports add no fixed segment silence. Historical tasks keep their recorded model/intervals. See the [pause comparison](docs/en/11-pause-comparison.md).

Users describe goals in natural language. Skills and local scripts handle work without deploying an HTTP service. Scope follows content-production needs, not the upstream toolkit: reference speech only, without voice training, fine-tuning or dataset management. Models and inference settings are managed internally.

## Quick start

Give the complete repository to your agent and ask: “Install codoop-cast, set Chinese as my default artifact language, and prepare dependencies only when needed.” In a separate content folder, supply a topic/reference recording and request a full MP4. The agent handles assets and intermediates.

See [installation and first video](docs/en/28-install-and-first-video.md) for steps, fallback installation and examples. [Release readiness](docs/en/29-release-readiness.md) distinguishes implemented capabilities from native-host/clean-machine gaps. Original code uses [Apache-2.0](LICENSE); third-party boundaries are in [THIRD_PARTY.md](THIRD_PARTY.md).

## Documentation

| Document | Contents |
| --- | --- |
| [Voice usage](docs/en/08-running-voice.md) | Implementation, commands, dependencies and limits |
| [Voice validation](docs/en/09-voice-validation.md) | Actual synthesis, retries and untested scope |
| [Alignment plan](docs/en/12-alignment-implementation-plan.md) | Initial plan; current implementation is in subtitle usage |
| [Skill contracts](docs/en/13-skill-contracts.md) | Responsibilities, content hub, references and targeted changes |
| [Production schemas](docs/en/14-production-schema.md) | Schema draft, 72-second example and validation limits |
| [Alignment experiments](docs/en/15-alignment-validation.md) | Chinese previews, mixed-text failures and handoff gaps |
| [Subtitle usage](docs/en/16-subtitles-running.md) | Normalization mapping, independent CLI/setup and limits |
| [Batch queue](docs/en/24-batch-running.md) | Sequential projects, failure isolation, recovery and reports |
| [Project workflow](docs/en/23-produce-running.md) | Reuse, plans, recovery, assembly and export |
| [Script/audio adapter](docs/en/22-script-audio-adapter.md) | Paragraph identity, dual text and actual frontend mapping |
| [Narration writing](docs/en/21-script-running.md) | Spoken editing, source linkage, exports and duration estimates |
| [Project layout](docs/en/20-project-layout.md) | Canonical paths, versions, selections and registration |
| [Research usage](docs/en/19-research-running.md) | Online/local evidence, reports and validation boundaries |
| [Video skills](docs/en/18-video-skills-running.md) | Independent entries, setup, actual timing and installation tests |
| [First HTML sample](docs/en/17-html-video-validation.md) | Real-timebase portrait/landscape prototype |
| [Shared setup](docs/en/07-setup-skill-plan.md) | Common on-demand preparation/configuration/repair |
| [Compatibility](docs/en/06-compatibility.md) | Host adapters; NVIDIA, AMD and Mac stages |
| [Plugin experience](docs/en/05-plugin-experience.md) | Skill boundaries, setup, private data and acceptance |
| [Overall plan](docs/en/01-plan.md) | Scope, sequence, milestones and decisions |
| [Technology](docs/en/02-technology.md) | Candidates, tradeoffs and validation requirements |
| [Workflow/data](docs/en/03-workflow.md) | Dependencies, artifacts, timebase and recovery |
| [Voice implementation plan](docs/en/04-voice-implementation-plan.md) | First module, local inference and delivery |
| [Research module](docs/en/modules/research.md) | Accessible, sourced reports |
| [Writing module](docs/en/modules/script.md) | Report-to-spoken-text design |
| [Voice module](docs/en/modules/voice.md) | Profiles, synthesis and quality checks |
| [Alignment module](docs/en/modules/alignment.md) | Real-audio times and captions |
| [Video module](docs/en/modules/video.md) | Storyboards, assets, placeholders and rendering |

## Design conventions

- Every module accepts independent inputs/outputs and targeted reruns; starting from a topic is optional.
- Prefer local inference/material processing/rendering; current-topic research can access the web.
- Actual audio drives one timeline shared by captions/visuals.
- Retain intermediates/provenance with reuse and recovery.
- Pin dependencies per feature and report only actual host/hardware validation.

The accepted-script → local speech → aligned captions → animated HTML video chain runs. Storyboard/design can precede speech; precise timing compiles afterward. Research/writing retain source identities; project workflow and agent-driven batches are connected.

### Artifact language

Skill instructions are English, while setup's output_language controls deliverables through shared/project/task overrides. Tell the agent the desired language: [configuration](docs/en/25-language-configuration.md). Project documentation has English/Simplified Chinese editions; skill instructions/references remain English only.

### Automatic assets and shared data

The agent prepares/reuses media and tracks origin without manual manifests. Inputs can be existing files, local diagrams or available host image generation. Asset replacement affects visuals/export only: [asset management](docs/en/26-agent-assets.md).

Models/tools/profiles use private shared storage; content assets/videos stay in projects. [Shared data layout](docs/en/27-shared-data-layout.md) specifies naming, persistence/cache boundaries and versioning. Setup creates needed categories compatibly; doctor inspects them read-only.

Public skills use `codoop-*` entry names, including `codoop-setup`, `codoop-research`, `codoop-voice` and `codoop-produce`. See [naming and upgrade compatibility](docs/en/30-skill-naming.md).

Video production reads shared/project settings for language, orientation, resolution, fps, captions and avatar placement, then pins them in output-profile.json. Task-specific overrides are supported: [production configuration](docs/en/31-production-configuration.md).
