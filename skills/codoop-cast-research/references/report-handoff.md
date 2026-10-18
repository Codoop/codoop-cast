# Report files and local execution

Use `<plugin-root>/scripts/cast.ps1` on Windows, or compatible Python to run `<plugin-root>/runtime/codoop-cast/cast.py`. Reuse CODOOP_CAST_HOME or global `--root <data-directory>` before the command. Resolve paths from the actual plugin root, not the current working directory. Pass filenames as arguments, never interpolate report prose into shell code.

```text
doctor --feature authoring
setup --feature authoring
research validate --report-file <draft/report.json>
research export --report-file <draft/report.json> --output <new-delivery-directory>
```

Agent writes the draft; these commands validate/export it, and do not perform web search or generate prose. Export produces report.json, report.md, checks.json and declared snapshot files. Existing destinations are refused. JSON stdout includes task ID, report_state, warnings and output paths; status ready means the operation succeeded, and a partial report remains partial. Do not call it fully verified.

## Structured report

Read `schemas/report.schema.json` for exact fields. Unlike production's eight-artifact video package, this report stands alone; it does not require package.json or output-profile.json.

Envelope: schema_version 0.1.0, kind report, stable artifact_id, revision, data.

Data:
- topic, audience, as_of (YYYY-MM-DD), mode online/offline, state ready/partial and scope_summary.
- summary `{text, claim_ids}` and sections `{id, title, paragraphs: [{text, claim_ids}]}`. Every substantive assertion should have a matching claim; structural validation cannot detect uncited assertions hidden inside prose. All ready-report paragraphs must reference existing claims.
- claims `{id, text, kind: fact|inference|disputed, evidence_ids, limitations}`. An inference cites its premises and explicitly says it is an inference in the prose. Disputed claims retain competing claims/sources and describe disagreement. Unsupported tentative claims are permitted only in partial reports with explicit limitations; never present them as established facts.
- sources `{id, title, url, source_type: webpage|local, accessed_at, published_at, read_status: full|excerpt|metadata|unavailable, snapshot_path, snapshot_sha256, notes}`. URL, published_at and snapshot fields may be null when unknown/unavailable. accessed_at is an actual ISO datetime; published_at is a known YYYY-MM-DD or null, never substituted with crawl date. For local material, preserve a useful original filename/description in notes without leaking private absolute paths into public exports.
- evidence `{id, source_id, text, kind: quote|paraphrase, locator}`. Locator identifies a heading, paragraph, page or line. Only full/excerpt sources can support evidence. A paraphrase is not an exact quotation. Search metadata alone is not evidence.
- unknowns `{id, question, impact}` and conflicts `{id, claim_ids, description}`. Conflicts link at least two distinct existing claims. Empty arrays are appropriate when no such issue is found; do not invent disagreements for completeness.

`full` means the relevant document was actually read in full; `excerpt` means only selected passages were read. Either requires a retained local snapshot. The snapshot can be a short evidence note with URL/locator and faithful paraphrase; its notes must say this is not the original full document. Use relative paths such as `sources/s-mdn.md` beneath the report directory and record SHA-256 of their exact bytes. Do not fabricate saved originals, publication dates or archive completeness. Unread sources require a reason and cannot support claims. Offline mode may cite URLs already present in local material without fetching them.

A ready report has supported core claims and no hidden evidence gaps; bounded unanswered questions and explicit disagreements may remain. Mark state partial if source access/coverage prevents answering the main question, or important claims remain unsupported. Validation can enforce missing-reference/evidence rules but cannot infer editorial completeness or independent corroboration.

## Downstream use

report.json is the canonical handoff; report.md is generated for reading. The codoop-cast-script skill maps each narration paragraph's `claim_ids` to report claims, retaining report artifact_id/revision in data.source. It must preserve uncertainty and not invent new facts merely to improve the hook. No narration text or final duration is created by this skill. Review referenced sources only when missing, stale or changed; there is no requirement to repeat all searches.
