"""Portable, immutable asset collections prepared by the host agent."""
from pathlib import Path
import re
import shutil

from .common import CastError, digest, new_id, read_json, write_json


def require(value, message):
    if not value:
        raise CastError('invalid_assets', message)


def local(folder, value):
    path = (folder / value).resolve()
    require(not Path(value).is_absolute() and path.is_relative_to(folder) and path.is_file(), 'Unavailable or escaping asset path: ' + str(value))
    return path


def validate(assets_file):
    path = Path(assets_file).expanduser().resolve()
    data = read_json(path)
    require(isinstance(data, dict) and set(data) == {'schema_version', 'kind', 'artifact_id', 'revision', 'data'}, 'Invalid asset envelope fields.')
    require(data.get('kind') == 'assets' and data.get('schema_version') == '0.1.0', 'Expected an assets artifact.')
    require(isinstance(data.get('artifact_id'), str) and bool(data['artifact_id']) and type(data.get('revision')) is int and data['revision'] > 0, 'Invalid asset identity.')
    require(isinstance(data.get('data'), dict) and isinstance(data['data'].get('items'), list), 'Expected asset items.')
    require(set(data['data']) == {'items'}, 'Unknown asset data fields.')
    seen = set()
    for item in data['data']['items']:
        require(isinstance(item, dict), 'Expected an asset record.')
        require(set(item) <= {'id', 'path', 'sha256', 'origin', 'usage_notes', 'provenance'}, 'Unknown asset fields.')
        require(isinstance(item.get('id'), str) and item['id'] and item['id'] not in seen, 'Missing or duplicate asset ID.')
        seen.add(item['id'])
        require(all(isinstance(item.get(k), str) and item[k].strip() for k in ('path', 'sha256', 'origin', 'usage_notes')), 'Asset needs path, hash, origin and usage notes.')
        file = local(path.parent, item['path'])
        require(digest(file) == item['sha256'], 'Asset hash mismatch: ' + item['id'])
        if 'provenance' in item:
            require(isinstance(item['provenance'], dict), 'Provenance must be an object.')
            validate_provenance(item['provenance'])
    return dict(status='ready', assets=str(path), items=len(seen), reference=dict(artifact_id=data['artifact_id'], revision=data['revision']))


def validate_provenance(value):
    if value is None:
        return
    fields = {'source_type', 'source_url', 'license', 'license_url', 'creator', 'generator', 'prompt', 'created_at'}
    require(isinstance(value, dict) and set(value) <= fields and all(isinstance(v, str) for v in value.values()), 'Invalid provenance fields.')
    require(value.get('source_type') in ('user', 'generated', 'local', 'web', 'code'), 'Declare the actual asset source type.')


def build(manifest_file, output, previous=None):
    source = Path(manifest_file).expanduser().resolve()
    folder = Path(output).expanduser().resolve()
    require(not folder.exists(), 'Use a new asset output directory.')
    manifest = read_json(source)
    require(isinstance(manifest, dict) and isinstance(manifest.get('items'), list), 'Manifest needs an items array; an empty array is valid.')
    if previous:
        validate(previous)
        old = read_json(previous)
    else:
        old = None
    files, items, ids = {}, [], set()
    for entry in manifest['items']:
        require(isinstance(entry, dict), 'Expected a manifest item.')
        ident = entry.get('id', '')
        require(isinstance(ident, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', ident) and ident not in ids, 'Use unique lowercase ASCII hyphenated asset IDs.')
        ids.add(ident)
        require(all(isinstance(entry.get(k), str) and entry[k].strip() for k in ('source_file', 'origin', 'usage_notes')), 'Declare source_file, origin and usage_notes.')
        original = (source.parent / entry['source_file']).expanduser().resolve()
        require(original.is_file(), 'Missing local source file: ' + str(original))
        sha = digest(original)
        require(not entry.get('sha256') or entry['sha256'] == sha, 'Source hash differs from expected content: ' + ident)
        suffix = original.suffix.lower()
        suffix = suffix if re.fullmatch(r'\.[a-z0-9]{1,10}', suffix) else '.bin'
        relative = 'media/' + sha + suffix
        item = dict(id=ident, path=relative, sha256=sha, origin=entry['origin'], usage_notes=entry['usage_notes'])
        if 'provenance' in entry:
            require(isinstance(entry['provenance'], dict), 'Provenance must be an object.')
            validate_provenance(entry['provenance'])
            item['provenance'] = entry['provenance']
        files[relative] = original
        items.append(item)
    artifact = dict(schema_version='0.1.0', kind='assets', artifact_id=old['artifact_id'] if old else new_id(),
                    revision=old['revision']+1 if old else 1, data=dict(items=items))
    folder.mkdir(parents=True)
    for name, original in files.items():
        target = folder/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        require(digest(target) == name.split('/')[1].split('.')[0], 'Source changed while copying; discard the incomplete candidate and retry in a new directory.')
    write_json(folder/'assets.json', artifact)
    return validate(folder/'assets.json')


def attach(assets_file, package):
    checks = validate(assets_file)
    source = Path(assets_file).expanduser().resolve()
    target = Path(package).expanduser().resolve()
    require(target.is_dir(), 'Provide an existing mutable working package.')
    require(not any((p/'version.json').exists() for p in (target, *target.parents)), 'Registered versions are immutable; copy to a new working package first.')
    artifact = read_json(source)
    payloads = {}
    for item in artifact['data']['items']:
        destination = (target/item['path']).resolve()
        require(destination.is_relative_to(target), 'Asset escapes working package.')
        require(not destination.exists() or destination.is_file() and digest(destination) == item['sha256'], 'Conflicting working resource: ' + item['path'])
        payloads[destination] = local(source.parent, item['path'])
    require(source != target/'assets.json', 'The source collection must be separate from the working package.')
    for destination, original in payloads.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copyfile(original, destination)
    write_json(target/'assets.json', artifact)
    return dict(status='ready', package=str(target), items=checks['items'], reference=checks['reference'],
                index_required=True, next_action='Update storyboard/scene asset references and IDs, increment changed revisions, then project index and scenes validate. Never edit registered versions.')
