"""Shared artifact-language configuration; independent of model environments."""
import re
from pathlib import Path

from .common import CastError, lock, read_json, root_path, write_json

RELATIVE = Path('.codoop-cast/config.json')


def language_tag(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:auto|[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*)', value):
        raise CastError('invalid_language', 'Use auto or a BCP 47 language tag such as zh-CN or en-US.')
    parts = value.split('-')
    return '-'.join([parts[0].lower()] + [p.title() if len(p) == 4 else p.upper() if len(p) == 2 else p for p in parts[1:]])


def resolve(directory=None, override=None, data_root=None):
    """Nearest local config, private global config, legacy project, then auto."""
    start = Path(directory or Path.cwd()).expanduser().resolve()
    if start.is_file():
        start = start.parent
    if override is not None:
        return dict(output_language=language_tag(override), source='task')
    legacy = None
    for folder in (start, *start.parents):
        path = folder / RELATIVE
        if path.is_file():
            data = read_json(path)
            if data.get('schema_version') != 1:
                raise CastError('invalid_config', 'Unsupported configuration version: ' + str(path))
            if 'output_language' in data:
                return dict(output_language=language_tag(data['output_language']), source=str(path))
        marker = folder / 'cast-project.json'
        if legacy is None and marker.is_file():
            legacy = read_json(marker).get('defaults', {}).get('language')
    path = Path(data_root or root_path()) / 'config.json'
    if path.is_file() and 'output_language' in (data := read_json(path)):
        return dict(output_language=language_tag(data['output_language']), source=str(path))
    return dict(output_language=language_tag(legacy) if legacy else 'auto', source='legacy-project' if legacy else 'default')


def configure(directory=None, output_language=None, data_root=None):
    """Omitted language preserves existing settings. No environment downloads."""
    from .data_layout import initialize
    initialize(data_root or root_path())
    folder = Path(directory).expanduser().resolve() if directory else Path(data_root or root_path())
    path = folder / RELATIVE if directory else folder / 'config.json'
    with lock(folder / '.cast' if directory else folder, 'configuration'):
        data = read_json(path) if path.exists() else dict(schema_version=1)
        if data.get('schema_version') != 1:
            raise CastError('invalid_config', 'Unsupported configuration version: ' + str(path))
        if output_language is not None:
            data['output_language'] = language_tag(output_language)
        elif 'output_language' not in data:
            data['output_language'] = resolve(directory, data_root=data_root)['output_language']
        write_json(path, data)
    return dict(status='ready', config=str(path), **resolve(directory, data_root=data_root))


def speech_language(value):
    tag = language_tag(value)
    primary = tag.split('-')[0]
    if primary not in ('zh', 'en'):
        raise CastError('unsupported_speech_language', 'This voice/alignment integration currently supports zh and en. Resolve auto to a concrete task language first; other languages remain available for agent-authored content.')
    return primary


def artifact_language(artifact, fallback='zh'):
    return language_tag(artifact.get('data', {}).get('language', fallback))


def check_artifact_language(artifact, directory=None, override=None, data_root=None):
    actual = artifact_language(artifact)
    if actual == 'auto':
        raise CastError('unresolved_language', 'Record the concrete language in data.language, not auto.')
    expected = resolve(directory, override, data_root)['output_language']
    aliases = {'zh': 'zh-CN', 'zh-Hans': 'zh-CN', 'en': 'en'}
    if expected != 'auto' and aliases.get(actual, actual) != aliases.get(expected, expected):
        raise CastError('language_mismatch', 'Artifact language ' + actual + ' differs from target ' + expected + '. Have the agent author a translated revision; changing a tag does not translate content.')
    return actual
