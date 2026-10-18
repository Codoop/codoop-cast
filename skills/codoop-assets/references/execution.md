# Local asset collections

The asset commands use the shared stdlib runtime and download no models. Actual image generation is performed by a capable host agent, not by this CLI. Work in `.cast/work/<task-id>/`; place completed collections at the next `project path --stage assets` candidate. Preserve fixed ASCII output names; do not translate schema keys or IDs.

Write a UTF-8 draft manifest. `source_file` may point to an existing user file, a local agent-generated image, or a file created by code. Relative source paths resolve against the draft manifest, and absolute source paths are supported for imports. Only imported copies belong in the output collection.

```json
{
  "items": [
    {
      "id": "topic-overview",
      "source_file": "visual.svg",
      "origin": "Created locally by the agent as an explanatory diagram",
      "usage_notes": "Overview scene; illustrative, not source evidence",
      "provenance": {
        "source_type": "code",
        "creator": "Host agent",
        "license": "Project-created diagram"
      }
    }
  ]
}
```

`provenance` is optional for legacy assets. New records should use it when relevant: `source_type` is `user`, `generated`, `local`, `web` or `code`; optional string fields are `source_url`, `license`, `license_url`, `creator`, `generator`, `prompt`, `created_at`. Record known information only. Optional input `sha256` pins expected source bytes. Empty `items` means no external material is needed, not an unfinished request.

```text
assets build --manifest-file <draft.json> --output <new-assets-version>
assets build --manifest-file <revised-draft.json> --previous <old-assets.json> --output <new-assets-version>
assets validate --assets-file <new-assets-version>/assets.json
project register --directory <project> --stage assets --version <vNNN> --depends-on storyboard=<vNNN>
assets attach --assets-file <new-assets-version>/assets.json --package <mutable-scene-package>
project index --package <mutable-scene-package>
scenes validate --package <mutable-scene-package>
```

For a production run use `produce start/checkpoint` as for other stages; checkpoint selects the registered version. For standalone preparation register only actual dependencies and select only when appropriate to the authorized task.

Build copies content into `media/<sha256>.<extension>`, reuses the same content path for identical files, and writes portable `assets.json`. A prior artifact preserves its artifact ID and increments revision. Asset semantic IDs come from the manifest; keep IDs stable when substituting a visual. Existing outputs are never overwritten. A failed copy leaves an incomplete candidate to inspect, not a successful stage.

Attach rejects registered version directories and conflicting local files. It copies the collection into a mutable scene package and replaces its `assets.json`; it deliberately does not guess editorial references. Before indexing, update `video-script.data.assets`, `scene.data.assets`, scene `asset_ids` and actual HTML resource paths to the attached collection. Increment changed artifact revisions and update their dependent references, including `scene.data.video-script`. The scene package can contain a derived storyboard revision without modifying its registered upstream storyboard. Retain only declared assets and needed local resources; do not accidentally ship private input files. Validation must pass before registering scenes.

For replacement, plan with `produce plan --force assets`. This rebuilds assets, affected scenes and exports while reusing narration and subtitles. A scene-only style edit can use `--force scenes` and reuse the selected collection. The renderer still validates local file hashes and package-relative resources.
