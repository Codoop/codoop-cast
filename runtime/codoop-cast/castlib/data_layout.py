"""Versioned shared-data layout. Existing payload paths remain unchanged."""
from pathlib import Path
from .common import CastError, lock, read_json, write_json

DIRECTORIES = {
    'python': 'Private Python distributions managed by uv',
    'envs': 'Feature environments: voice, alignment, authoring, video',
    'engines': 'Pinned upstream engine source trees',
    'models': 'Downloaded model resources; engine-required resources may also live inside engines',
    'tools': 'Shared executables, including uv and FFmpeg',
    'browsers': 'Feature-scoped browser installations',
    'features': 'Feature installation state and integrity records',
    'voices': 'Persistent speaker profiles and reference recordings, keyed by 32-character IDs',
    'jobs': 'Engine task records and intermediate outputs, keyed by 32-character IDs',
    'logs': 'Feature setup and task logs',
    'cache': 'Rebuildable downloads and tool caches; not voices or final project assets',
    'locks': 'Runtime coordination locks',
}
MARKER = 'data-layout.json'


def inspect(root):
    root = Path(root).expanduser().resolve()
    marker = root/MARKER
    if marker.exists():
        saved = read_json(marker)
        if saved.get('kind') != 'cast-data-layout' or saved.get('schema_version') != 1:
            raise CastError('unsupported_data_layout', 'Unsupported shared data layout. Keep existing files and inspect the marker before setup.')
    known = set(DIRECTORIES) | {'config.json', MARKER}
    return dict(schema_version=1, root=str(root), marker=str(marker), registered=marker.is_file(),
                directories={name:dict(path=str(root/name), exists=(root/name).is_dir(), purpose=purpose) for name,purpose in DIRECTORIES.items()},
                unmanaged_entries=sorted(p.name for p in root.iterdir() if p.name not in known) if root.is_dir() else [])


def initialize(root):
    root = Path(root).expanduser().resolve()
    with lock(root, 'data-layout'):
        state = inspect(root)
        if not state['registered']:
            write_json(root/MARKER, dict(schema_version=1, kind='cast-data-layout', directories=list(DIRECTORIES)))
    return inspect(root)
