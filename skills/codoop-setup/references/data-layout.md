# Shared data layout, version 1

The selected private data root is shared across content projects. Resolve it consistently through global `--root`, `CODOOP_CAST_HOME`, then the platform default. The launcher and worker must use the same root. The root folder's display name is user-selectable; internal managed names are fixed ASCII.

`data-layout.json` records format version 1; `config.json` stores shared preferences. Canonical top-level directories and owners are declared in `<plugin-root>/runtime/codoop-cast/castlib/data_layout.py`:

- `python/`: private uv-managed interpreters; `envs/<feature>/`: feature-specific environments.
- `engines/<engine>/`: pinned upstream source and engine-required resources; `models/<model>/`: other downloaded models. Respect upstream resource locations rather than duplicating them.
- `tools/`: uv and FFmpeg; `browsers/<feature>/`: pinned browser resources.
- `features/<feature>.json`: integrity/install state, not user preferences.
- `voices/<32-hex-id>/`: persistent reference recording, selected reference audio and voice metadata.
- `jobs/<32-hex-id>/`: task state, pinned inputs and engine outputs. Read actual paths from job records; do not infer output filenames.
- `logs/`: setup/task logs; `locks/`: active runtime coordination.
- `cache/`: downloads, tmp, uv, pip, huggingface and nltk caches. Child temporary files use `cache/tmp/`.

Create only needed directories. New features reuse these categories, register their own feature/environment names and update the layout declaration for any truly new root category. Keep source/plugin installation, shared runtime data and portable content projects separate. Final content belongs in project stage versions; it may be copied from shared job outputs.

Setup adds the layout marker to existing roots without moving or deleting payloads. Doctor reports the layout read-only and lists unmanaged root entries for inspection; unknown files are not permission to remove them. Future unsupported marker versions must not be overwritten. Never silently migrate a root or claim that changing its path moves existing absolute-path records.

Preserve `voices`, `jobs` and `config.json`. No automatic cleanup or migration command is implemented. Do not delete the root or an active cache/lock to repair one dependency; use targeted shared setup. Do not store project asset collections, exported videos or unrelated software at the root.
