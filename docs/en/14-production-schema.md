# Minimal production package v0.1.0

[English](14-production-schema.md) | [简体中文](../zh-cn/14-production-schema.md)

> Historical schema/validation record. Current status: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

Initial status: draft and verifiable example, not a released runtime protocol. Schemas live in `schemas/`, example in `examples/72-second-workflow/`. The CLI did not yet automatically read/write the format; voice/alignment/scene integration would refine it.

A later subtitle update emitted script/audio/alignment fragments. Optional `span_basis` selects `spoken_text` or `display_text`; missing means legacy spoken_text. Formal caption exports explicitly use display_text, while audio spans still use actual spoken_text. Full-package import/video was pending at that intermediate stage.

Every artifact has `schema_version`, `kind`, `artifact_id`, `revision`, `data`. The protocol version and artifact revision are different; semantic objects keep stable IDs unless replaced.

Separate schemas cover script, video-script, assets, scene, audio, alignment, timeline and output-profile. The minimal example has one of each, indexed by relative path/SHA-256 in package.json. An individual skill consumes only declared prerequisites; requiring all eight is this end-to-end validator's rule, not a universal input requirement.

Script owns prose; storyboard references paragraphs. Audio chunks reference actual spoken_text via Unicode-codepoint `[start,end)` `script_spans`, not UTF-8 bytes or JavaScript UTF-16 indices. JavaScript adapters must convert explicitly. Initial scene/event anchors use paragraph boundaries; adding word ranges requires schema changes and repeated-word tests.

Audio offsets come from actual export manifests. Alignment uses the same sample timebase with unit/cue boundaries. Display times, frames and SRT milliseconds are derived, never evenly allocated by character count. Validate script/chunk mappings rather than assuming matching IDs prove identity.

The `render-at-time-v1` target is the same scene version/layout/time producing the same visible result. This draft only specifies intent; HTML entry functions, loading/fonts/random seeds need rendering validation. It does not imply arbitrary websites can export as video.

Pending alignment/blocked timeline may be valid planning outputs, never render-ready. Checks cover schemas, hashes, typed/versioned references, IDs, mappings, timing/order, event targets, resource containment and avatar bounds. They do not replace content coverage, complete dependency scans, real media duration checks or viewing.

Pending at this stage: external adapters, full word/number display mapping, standard audio fingerprints/model metadata, post-rounding SRT checks, complex transition tracks, font/platform safe areas, aspect relayout and runtime integration. Initial timelines have nonoverlapping scenes; do not generalize that simplification to all future tracks.

Next steps were real alignment and minimal HTML. Speech/profile changes invalidate outputs through references/digests; update only affected revisions/references.
