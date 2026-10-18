# Commands and artifact handoff

```text
video compile --package <source-package> --output <new-compiled-directory> [--accept-reviewed-alignment]
video check --package <compiled-directory> --output <new-check-name.mp4>
video render --package <compiled-directory> --output <new-video.mp4>
task status --job <task-id>
task cancel --job <render-task-id>
```

Outputs must use new paths; prior work is preserved. Commands return JSON on stdout and task/log information on stderr. Run foreground jobs with host long-process support. Check commands produce a `<name>-qa` directory and no MP4. Inspect render.json and screenshots. Final rendering supports cancellation between frames; resume is not yet implemented.

All artifact envelopes use schema_version 0.1.0, kind, artifact_id, revision and data. References contain exact artifact_id and revision. `project index` explicitly refreshes canonical artifact filenames and hashes after agent edits; it does not bump revisions or certify editorial correctness. Validation rejects stale references and resources escaping the package. Use the JSON schemas as authoritative field definitions.

Compilation copies declared artifacts, scene entries, assets, actual audio and known supplemental files into the new package, then creates timeline.json. Declare supporting HTML resources as assets; undeclared files are not copied. Rendering is offline file:// Chromium capture with FFmpeg H.264/AAC MP4. Current private installers are verified on Windows; AMD and macOS remain unverified. Video encoding uses CPU and does not itself require CUDA. The audio/alignment feature has separate hardware requirements.
