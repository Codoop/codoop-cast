# Commands and artifact handoff

```text
project index --package <authoring-directory>
scenes validate --package <authoring-directory>
scenes check --package <authoring-directory> --output <new-preview-name.mp4>
```

Outputs must use new paths; prior work is preserved. Commands return JSON on stdout and task/log information on stderr. Run foreground jobs with host long-process support. Check commands produce a `<name>-qa` directory and no MP4. Inspect render.json and screenshots. Final rendering supports cancellation between frames; resume is not yet implemented.

All artifact envelopes use schema_version 0.1.0, kind, artifact_id, revision and data. References contain exact artifact_id and revision. `project index` explicitly refreshes canonical artifact filenames and hashes after agent edits; it does not bump revisions or certify editorial correctness. Validation rejects stale references and resources escaping the package. Use the JSON schemas as authoritative field definitions.

## render-at-time-v1

Expose `window.CodoopCast` with:
- `ready`: promise resolving when local images/fonts and application setup are ready.
- `configure(bundle)`: receives full artifact envelopes profile, timeline, alignment, storyboard, assets, plus asset_base_url, audio_url and preview_only. Optional visuals is topic-specific supplemental data, not a required framework format. Do not use audio playback as the render clock.
- `renderAt(seconds)`: select scene from timeline sample intervals, derive all element visibility/positions and active subtitle from that absolute time, and return `{scene_id: activeSceneId}`. Repeated calls and backwards seeks must reconstruct the same state. Events are absolute samples. No Date.now, randomness, requestAnimationFrame-driven motion or uncontrolled CSS animation in render mode.
- `inspect()`: return `{issues: []}` only after actually checking visible text bounds, safe areas, required elements and avatar/caption overlap. Return descriptive issues for failures. Do not hard-code an empty result.
- `snapshot()`: return serializable visible state or the scene root's outerHTML so repeatability checks work for any DOM structure.

Use profile width/height/fps and subtitle_style for captions. Strip punctuation at caption tails only; keep internal punctuation and meaningful symbols. Use avatar enabled/mode/x/y/width/height; normalized coordinates refer to the full frame. Exclude placeholder when disabled. Ensure scene content leaves room for the selected caption/avatar positions. In `?render=1` mode avoid autoplay or interactive controls. Local preview may use an audio clock; exported frames always use renderAt.

The visual preview supplies synthetic 5-second scene intervals and marks screenshots as illustrative. Support empty alignment/cues and no audio in this mode. It does not create persisted final timing. A complete production package can later use `video check` for actual synchronization.
