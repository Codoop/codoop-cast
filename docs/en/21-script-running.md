# Narration-writing skill usage

[English](21-script-running.md) | [简体中文](../zh-cn/21-script-running.md)

> Historical implementation record. Current state: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

On 2026-10-17 `codoop-cast-script` gained independent standard-report or UTF-8 Markdown/text input. The agent writes, and private authoring validates/exports. Research invocation, voice models and HTTP are unnecessary.

## User requests

“Turn this report into narration,” “around one minute,” or “keep these points, make it natural.” Read the selected project report or explicit external input, explain for the audience/length and deliver reviewable prose. Do not invent a duration requirement when unspecified.

Preserve facts, numbers, units, conditions, attribution, inference and disputed boundaries. Avoid exaggerated hooks, fabricated experiences and empty endings. Humanizer-zh is an optional writing reference, not a bundled/mandatory installation. Project-specific narration guidance ships independently, without AI-detector claims.

## Outputs

```text
script/vNNN/
  version.json        # project registration
  script.json         # stable paragraph IDs, display_text, spoken_text, claim_ids
  script.md           # readable body, separate production notes afterward
  script.txt          # display/original text only: no heading, citations or notes
  spoken.txt          # speech only; defaults to display text
  script-source.json  # input/script hashes, relative paths, script identity
  checks.json         # structure, provenance, duration estimate, limits
  inputs/             # actual report and declared evidence snapshots
```

New `data.source` pins report artifact_id/revision or external-file SHA-256. It is optional for legacy schema compatibility but required for new writing exports. Standard-report paragraphs need valid claim_ids. External reports without structured claims use empty lists and disclose no independent fact verification.

Edits retain paragraph IDs; splits/merges get new IDs with provenance explaining relationships. Increment script revision, not every input revision to match a directory number.

## Commands

Use the shared PowerShell/Python entry; global `--root` precedes subcommands.

```text
script validate --script-file <draft/script.json> --source-file <report.json-or-report.md-or-report.txt>
script export --script-file <draft/script.json> --source-file <report> --output <project/script/vNNN> [--target-seconds 60]
script validate --script-file <exported/script.json>
project register --directory <project> --stage script --version vNNN --depends-on research=vMMM
```

Use new outputs, retain old results. Export includes source copies and remains verifiable without original drafts. Registration/selection follow project rules; pending candidates do not replace accepted prose automatically.

Commands do not run a writing model or establish factual fidelity merely from valid IDs. The agent checks source numbers/conditions/meaning. Partial/unverified sources remain disclosed in checks/production notes.

## Duration/downstream

Count Unicode letters/numbers in spoken_text and divide by an assumed rate. Default 4 characters/second is an explicit editing assumption, not measured model behavior; adjust with `--characters-per-second`. Pauses/actual numeric or English readings are omitted, especially weakening mixed-text estimates. `--target-seconds` records intent, not achieved duration. Edit toward the goal; real audio determines final time.

`storyboard prepare --script-file` preserves identity/paragraphs. At this historical stage voice accepted only text; script.txt was original input and attempts recorded frontend normalization. Distinct spoken.txt must not silently replace display prose/IDs. The identity-preserving adapter was pending, and this writing run did not synthesize audio. See the subsequent [adapter](22-script-audio-adapter.md).

Keep natural script punctuation for meaning/pauses; removing caption-tail punctuation is only a display rule. Writing does not assign precise subtitle/scene times.

## Validation

- Twelve new contracts: portable source retention/identity, stale report/bad claims, duplicate/empty paragraphs, unverified external material/no invented claims, tampered retained source, partial, storyboard import, output preservation, invalid durations.
- Eighty-five tests then passed: 50 ordinary/35 contracts.
- Eight skill checks passed; installed validation read self-contained exports without original drafts.
- A real subtitle-timing report produced three paragraphs in sample script/v002 with research/v001 dependency. v001 tested duration recording; v002 omitted a target, estimated ~41.5 seconds, not actual audio. Neither candidate was labeled user-reviewed/selected at that point.
- Existing eight-artifact contracts remained valid without extra mandatory dependencies.

Style/pacing still needed user feedback. Full workflow then needed identity-preserving speech, assets and orchestration/batch. Schema validation is not general factual-consistency evaluation. Later structured speech/dual ranges/original IDs and stress-alignment failures are recorded in the adapter guide.
