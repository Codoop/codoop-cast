# Commands and handoff

Use `<plugin-root>/scripts/cast.ps1` on Windows or compatible Python with `<plugin-root>/runtime/codoop-cast/cast.py`. Global --root precedes the command; reuse the configured data root. Do not hard-code developer paths or insert prose into shell code. Long text lives in UTF-8 files.

```text
script validate --script-file <draft/script.json> --source-file <report.json-or-report.md-or-report.txt> [--target-seconds <seconds>]
script export --script-file <draft/script.json> --source-file <report.json-or-report.md-or-report.txt> --output <project/script/vNNN> [--target-seconds <seconds>]
script validate --script-file <exported/script.json>
```

Agent authors the script; these commands do not write prose or call a model. They use the existing lightweight authoring feature. Export rejects an existing destination. It preserves the script identity and produces script.json, script.md, script.txt, spoken.txt, script-source.json, checks.json and inputs/ containing the actual source plus declared research evidence snapshots. Standalone validation of an exported package uses script-source.json and retained source hashes; no original source path is required.

## Script format

Read schemas/script.schema.json. Envelope: schema_version 0.1.0, kind script, artifact_id, revision and data. Data contains language, provenance (a concise source/editing explanation), paragraphs, and source for new script exports:

- Research source: `{kind: "report", artifact_id: "<actual-report-id>", revision: <actual-report-revision>}`.
- External report: `{kind: "external", sha256: "<SHA-256-of-exact-file-bytes>"}`.

The source field is optional in the common schema so older video/subtitle artifacts remain compatible; this new exporter requires it. External JSON must be a report artifact; generic external documents use .md/.txt. Preserve exact actual source identity instead of relabeling it to match the current folder version.

Each paragraph has id, display_text, spoken_text and claim_ids. Report-based paragraphs cite existing claims; external reports without structured claims use an empty claim_ids list and remain unverified. Never invent claim IDs to make validation pass. Use stable lowercase ASCII IDs (e.g. p-subtitle-clock); retain imported existing IDs on revision. A rewritten paragraph keeps its ID if it has the same semantic role; splitting/merging creates new IDs. Editing increments the script revision, not the source report revision.

script.txt joins display_text paragraphs with blank lines and contains no headings, links or production notes. spoken.txt similarly joins spoken_text. script.md shows the readable narration plus separate production notes. Source links/claims remain in structured data and retained reports; they do not become words the speaker must read.

## Duration

Optional --target-seconds records the requested target. --characters-per-second defaults to 4.0 and can be overridden with a justified assumption. The estimator counts Unicode letters/numbers in spoken_text and divides by that assumed rate; it ignores punctuation, pauses and actual acronym/number pronunciation. This is a rough editing aid, particularly weak for mixed languages, not a measured rate or a guarantee. checks.json labels it estimated and records the method and inputs. No precise timestamps, scene durations or subtitle files are inferred from this estimate.

## Downstream

storyboard prepare --script-file <script/vNNN/script.json> --output <new-storyboard-directory> preserves the script and paragraph IDs. Voice now accepts `speech generate --script-file <script.json>`; prefer it over flattening the script to text. Both original text forms and claim references survive synthesis and subtitle generation. The original artifact is not rewritten to contain frontend-normalized numbers.

When a pronunciation changes actual characters, add paragraph.pronunciation_spans containing ordered Unicode codepoint ranges display_start/display_end/spoken_start/spoken_end. Agent calculates indices from the agreed text; the user need not manage them. Numeric/punctuation changes can use the conservative automatic mapping. Each explicit range is indivisible for timing; arbitrary rewrites without a mapping are rejected. The common script schema accepts this optional field. Script export still does not synthesize audio or imply listening approval.

Validation detects missing/stale source identity, changed retained source, empty/duplicate paragraphs and nonexistent claim references. It cannot detect a changed fact merely because the paragraph still cites a valid claim. Agent must compare wording, numbers and caveats against source text. Research partial/unverified inputs remain explicit in checks and production notes. Directory registration and selection use shared project commands after export; they do not replace editorial review.
