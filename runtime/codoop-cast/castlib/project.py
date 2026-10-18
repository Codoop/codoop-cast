"""Local content projects: fixed stage paths, immutable registered versions, explicit selection."""
import re
from pathlib import Path

from .video_config import resolve_video
from .config import resolve
from .common import CastError, digest, lock, new_id, read_json, write_json

MARKER = 'cast-project.json'
STAGES = {
    'research': ('report.json', 'report.md'),
    'script': ('script.json', 'script.txt', 'script.md'),
    'storyboard': ('video-script.json', 'storyboard.md'),
    'assets': ('assets.json',),
    'voice': ('narration.wav', 'narration.json'),
    'subtitles': ('alignment.json', 'subtitles.srt'),
    'scenes': ('scene.json',),
    'exports': ('video.mp4', 'production/package.json', 'video-qa/render.json'),
}


def require(value, message):
    if not value:
        raise CastError('invalid_project', message)


def version_number(value):
    require(bool(re.fullmatch(r'v[0-9]{3,}', value)), 'Use a version such as v001.')
    number = int(value[1:])
    require(number > 0 and value == f'v{number:03d}', 'Version must be canonical and start at v001.')
    return number


def inside(root, relative):
    path = (root / relative).resolve()
    require(not Path(relative).is_absolute() and path.is_relative_to(root), 'Project path escapes its root.')
    return path


def locate(directory=None):
    start = Path(directory or Path.cwd()).expanduser().resolve()
    require(start.is_dir(), 'Provide an existing project directory.')
    for candidate in (start, *start.parents):
        if (candidate / MARKER).is_file():
            data = read_json(candidate / MARKER)
            require(data.get('schema_version') == '0.1.0' and data.get('kind') == 'cast-project', 'Unsupported project format.')
            require(set(data.get('current', {})) == set(STAGES), 'Project must declare all current stage selections.')
            for stage, version in data['current'].items():
                if version is not None:
                    version_number(version)
                    inside(candidate, f'{stage}/{version}')
            return candidate, data
    raise CastError('project_not_found', 'No cast-project.json found. Initialize the user-selected content directory first.')


def initialize(directory, name=None):
    root = Path(directory).expanduser().resolve()
    if (root / MARKER).exists():
        found, _ = locate(root)
        return dict(status='ready', project=str(found), created=False)
    require(not any((p / MARKER).exists() for p in root.parents), 'Do not create a nested content project.')
    root.mkdir(parents=True, exist_ok=True)
    video = resolve_video(root)['video']
    data = dict(schema_version='0.1.0', kind='cast-project', project_id=new_id(), name=name or root.name,
                defaults=dict(language=resolve(root)['output_language'], output=dict(**video['resolution'], fps=video['fps'])),
                current={stage: None for stage in STAGES})
    with lock(root / '.cast', 'project'):
        require(not (root / MARKER).exists(), 'Project was initialized by another process; inspect it before retrying.')
        write_json(root / MARKER, data)
    return dict(status='ready', project=str(root), created=True)


def next_path(directory, stage):
    root, _ = locate(directory)
    require(stage in STAGES, 'Unknown project stage.')
    parent = inside(root, stage)
    maximum = 0
    if parent.exists():
        for entry in parent.iterdir():
            if re.fullmatch(r'v[0-9]{3,}', entry.name):
                maximum = max(maximum, version_number(entry.name))
    version = f'v{maximum + 1:03d}'
    return dict(status='ready', stage=stage, version=version, output=str(parent / version),
                required_files=list(STAGES[stage]), reserved=False)


def checked_record(root, stage, version):
    require(stage in STAGES, 'Unknown project stage.')
    version_number(version)
    folder = inside(root, f'{stage}/{version}')
    record = read_json(folder / 'version.json')
    require(record.get('schema_version') == '0.1.0' and record.get('kind') == 'stage-version'
            and record.get('stage') == stage and record.get('version') == version, 'Invalid stage version manifest.')
    require(record.get('state') in ('ready', 'partial'), 'Invalid registered version state.')
    for relative, expected in record['files'].items():
        path = inside(folder, relative)
        require(path.is_file() and digest(path) == expected, 'Registered output changed or is missing: ' + str(path))
    require(set(STAGES[stage]) <= set(record['files']), 'Stage version lacks required files.')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p != folder / 'version.json'}
    require(actual == set(record['files']), 'Registered version contains unrecorded files; create a new version.')
    for dependency in record['dependencies']:
        require(dependency['stage'] in STAGES, 'Unknown dependency stage.')
        version_number(dependency['version'])
    return record


def register(directory, stage, version, dependencies=(), state='ready'):
    root, _ = locate(directory)
    require(stage in STAGES and state in ('ready', 'partial'), 'Invalid stage or state.')
    version_number(version)
    folder = inside(root, f'{stage}/{version}')
    with lock(root / '.cast', 'project'):
        require(folder.is_dir() and not (folder / 'version.json').exists(), 'Use a completed, unregistered version directory.')
        require(all(inside(folder, name).is_file() for name in STAGES[stage]), 'Required stage files are missing.')
        refs = []
        for spec in dependencies:
            pair = spec.split('=')
            require(len(pair) == 2 and pair[0] in STAGES, 'Dependency format is stage=v001.')
            dep_stage, dep_version = pair
            require((dep_stage, dep_version) != (stage, version), 'A version cannot depend on itself.')
            checked_record(root, dep_stage, dep_version)
            require(not any(d['stage'] == dep_stage for d in refs), 'Duplicate dependency stage.')
            refs.append(dict(stage=dep_stage, version=dep_version,
                             sha256=digest(inside(root, f'{dep_stage}/{dep_version}/version.json'))))
        files = {}
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                relative = path.relative_to(folder).as_posix()
                files[relative] = digest(inside(folder, relative))
        require(all(inside(folder, name).stat().st_size > 0 for name in STAGES[stage]), 'Required stage files must not be empty.')
        write_json(folder / 'version.json', dict(schema_version='0.1.0', kind='stage-version', stage=stage,
                   version=version, state=state, dependencies=refs, files=files))
    return dict(status='ready', stage=stage, version=version, selected=False)


def select(directory, stage, version):
    root, _ = locate(directory)
    with lock(root / '.cast', 'project'):
        checked_record(root, stage, version)
        _, data = locate(root)
        data['current'][stage] = version
        write_json(root / MARKER, data)
    return dict(status='ready', stage=stage, version=version)


def inspect_project(directory=None):
    root, data = locate(directory)
    def inspect(stage, version, stack=()):
        key = (stage, version)
        require(key not in stack, 'Cyclic project dependencies.')
        record = checked_record(root, stage, version)
        reasons = []
        for dep in record['dependencies']:
            ds, dv = dep['stage'], dep['version']
            require(digest(inside(root, f'{ds}/{dv}/version.json')) == dep['sha256'], 'Dependency manifest changed.')
            if data['current'][ds] != dv:
                reasons.append(f'Uses {ds}/{dv}; selected version is {data["current"][ds] or "none"}.')
            reasons.extend(inspect(ds, dv, (*stack, key))[1])
        return record['state'], reasons
    stages = {}
    for stage, version in data['current'].items():
        if version is None:
            stages[stage] = dict(state='missing', version=None)
            continue
        try:
            state, reasons = inspect(stage, version)
            stages[stage] = dict(state='stale' if reasons else state, version=version,
                                 path=str(root / stage / version), reasons=list(dict.fromkeys(reasons)))
        except (OSError, ValueError, KeyError, TypeError, CastError) as exc:
            stages[stage] = dict(state='invalid', version=version, error=str(exc))
    return dict(status='ready', project=str(root), name=data['name'], defaults=data['defaults'], stages=stages)
