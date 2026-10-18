# Topic research usage

[English](19-research-running.md) | [简体中文](../zh-cn/19-research-running.md)

> Historical implementation record. Current status: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

On 2026-10-17 the independent research skill accepted a topic or local material without the video workflow. The user describes intent; the agent reads sources, organizes evidence, writes and invokes local export.

## Capabilities/boundaries

- Use existing host search/browsing, preferring primary sources. No required search provider, new web service or key.
- Offline mode reads supplied material and states its currency. Export does not fetch websites; first authoring setup may require dependency downloads, so prepare it ahead for strict offline use.
- Research installs no GPT-SoVITS, aligner or browser. Validation/export use lightweight shared authoring setup.
- Write for beginners: core answer, necessary concepts/examples, no mandatory chapter count or jargon padding. At this stage Chinese requests defaulted to Chinese reports; the shared language policy later generalized selection.
- Unread pages, snippets and unvisited links are not verified evidence. Deliver partial when material is insufficient; command success is not factual completeness.

## Outputs/handoff

`report.md` is readable; `report.json` carries stable claim IDs, fact/inference/dispute types, evidence, source metadata, as-of date, conflicts/unknowns. `checks.json` records structural checks/limits. `sources/` retains identified evidence notes/hashes, not invented full-page archives.

The report schema is independent, not a ninth mandatory video artifact. Downstream paragraph claim_ids can reference claims and retain report artifact_id/revision. Writing was unimplemented at this stage; research itself does not automatically create speech/scripts.

Sources resolve relative to the report with SHA-256. Read statuses distinguish full, excerpt, metadata and unavailable. Excerpt means only relevant portions read; short notes are not complete text. Access/publication dates are separate; unknown publication is null.

## Commands

Through `scripts/cast.ps1` or compatible Python and `runtime/codoop-cast/cast.py`:

```text
research validate --report-file <draft/report.json>
research export --report-file <draft/report.json> --output <new-delivery>
```

The agent authors the draft from actual research. Commands do not search, judge source quality or detect every assertion lacking structured citations. Export copies declared notes and renders Markdown. Preserve old directories; revisions use new outputs.

A starting bound is two search rounds/eight opened candidate sources, adjustable by scope, finishing early when answered. Eight is not a minimum per report. Preserve unresolved gaps instead of endless searching.

## Validation

- Eleven new research contracts: portable output, IDs, partial, unsupported/unread evidence rejection, snapshot hashes, escaping paths, bad refs, local material, output preservation.
- Sixty tests passed: 37 ordinary/23 contracts.
- Skill format validation passed.
- Real MDN WebVTT excerpts supported a report distinguishing directly sourced facts from mechanism-based inference: `examples/research-subtitle-timing`.
- Updated/copied export worked in isolated Chinese/space paths without changing actual user-agent installation.

This establishes validation/export, not every host's search, factual accuracy rate or native installation. Next steps then were writing, identity-preserving audio handoffs and full orchestration.
