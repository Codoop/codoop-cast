# Commands and artifact handoff

```text
storyboard prepare --text-file <narration.txt> --output <new-plan-directory>
storyboard prepare --script-file <script.json> [--profile-file <output-profile.json>] --output <new-plan-directory>
project index --package <plan-directory>
storyboard validate --package <plan-directory>
```

Outputs must use new paths; prior work is preserved. Commands return JSON on stdout and task/log information on stderr. Run foreground jobs with host long-process support. Check commands produce a `<name>-qa` directory and no MP4. Inspect render.json and screenshots. Final rendering supports cancellation between frames; resume is not yet implemented.

All artifact envelopes use schema_version 0.1.0, kind, artifact_id, revision and data. References contain exact artifact_id and revision. `project index` explicitly refreshes canonical artifact filenames and hashes after agent edits; it does not bump revisions or certify editorial correctness. Validation rejects stale references and resources escaping the package. Use the JSON schemas as authoritative field definitions.

video-script.data contains script and assets references, scenes, and events. Read video-script.schema.json for required fields. Scene anchors reference paragraph_id, edge start/end, offset_ms, and optional text_range. Preserve stable IDs when modifying only visual intent. Handoff: script.json, video-script.json, assets.json, output-profile.json, package.json and readable storyboard.md. No final timing is claimed.
