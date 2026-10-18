# English skills and configurable artifact language

[English](25-language-configuration.md) | [简体中文](../zh-cn/25-language-configuration.md)

Follow codoop-flow's `output_language`: retain the setup preference, with explicit task requests taking precedence. The nine skills present at this milestone, their instructions and agent metadata use English; that does not force English conversation or artifacts.

## Storage

Private data-root config.json holds defaults alongside feature settings. A project/batch can have `.codoop-cast/config.json`, inherited from the nearest ancestor. JSON reuses Python 3.10 stdlib/runtime without adding TOML dependencies.

```json
{
  "schema_version": 1,
  "output_language": "zh-CN"
}
```

The repository supplies `codoop-cast.config.example.json`. Users say “default to Chinese” or “this project in English”; setup writes settings, not users. Future initialization preferences extend the shared file. Repeat setup preserves known and unknown settings.

Precedence: explicit task → nearest ancestor config → private shared default → legacy project defaults.language → auto. Conversation language is unaffected.

## Commands

Use installed scripts/cast.ps1 or runtime/codoop-cast/cast.py, with global `--root` first.

```text
setup --output-language zh-CN
setup --directory <content-project-or-batch> --output-language en
config show --directory <content-project-or-batch>
config show --directory <content-project-or-batch> --language en-US
setup --feature voice
```

Setup without a feature saves configuration only, without business models/environments. Feature setup reuses shared preferences. Show with --language resolves a task override without saving it.

The agent resolves auto from explicit request, input content, then conversation; runtime does not guess chat intent. New report/script data.language must be concrete, and appropriate command invocations receive the resolved task language.

Research/script validate/export, speech generate, external subtitles generate, plain-text storyboard prepare, produce plan and batch report accept --language. Structured scripts/existing audio tasks retain their recorded language; a flag cannot relabel Chinese audio as English.

## Artifacts/workflow

Reports, narration, screen text, captions and notes follow the target. Preserve quotes/proper nouns/snapshots/URLs/IDs/schema keys/fixed ASCII names as appropriate. Runtime checks declarations against targets; the agent performs real translation. A language tag neither translates prose nor detects every sentence's actual language.

Language is versioned content. Translate into new revisions, retain accepted versions and rebuild affected audio/captions/visuals/exports. Produce pins target language; changed defaults require replan unless the run has an explicit task override. Do not reuse differently declared reports/scripts under a new target.

Legacy reports without language retain historical Chinese behavior; new agent outputs declare it. Old workflow plans remain readable. Old unconfigured batch reports retain Chinese; explicit auto needs an agent-resolved argument.

## Limits

Built-in report/script/batch/storyboard labels support Simplified Chinese/English. For other languages the agent can translate English keys in `castlib/locale.py` into `.codoop-cast/locales/<tag>.json`, preserving placeholders. Missing/incomplete labels fail rather than silently mixing Chinese.

Agents can author other languages; integrated speech/alignment currently routes zh/en only, rejecting others/unresolved auto before model setup. English argument/export checks passed, but no new English synthesis/listening established timbre/pronunciation/sync quality. Reference-recording language is independent.

All skills follow `skills/codoop-setup/references/language.md`, without per-skill competing language defaults.

References:

- https://github.com/Codoop/codoop-flow/blob/main/codoop_flow.toml.example
- https://github.com/Codoop/codoop-flow/blob/main/skills/codoop-init/SKILL.md
