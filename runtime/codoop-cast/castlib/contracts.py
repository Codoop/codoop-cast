"""Validate a draft production package. Requires jsonschema==4.23.0."""
import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMAS = Path(__file__).resolve().parents[3] / 'schemas'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(directory):
    directory = Path(directory).resolve()
    package = json.loads((directory / 'package.json').read_text(encoding='utf-8'))
    require(package['schema_version'] == '0.1.0', 'Unsupported package version')
    records, kinds = {}, {}
    for entry in package['artifacts']:
        relative = Path(entry['path'])
        path = (directory / relative).resolve()
        require(not relative.is_absolute() and path.is_relative_to(directory), 'Artifact escapes package')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], 'Artifact hash mismatch')
        artifact = json.loads(path.read_text(encoding='utf-8'))
        kind = artifact['kind']
        require(kind in {'script','video-script','assets','scene','audio','alignment','timeline','output-profile'}, 'Unknown artifact kind')
        schema = json.loads((SCHEMAS / (kind + '.schema.json')).read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(artifact)
        key = (artifact['artifact_id'], artifact['revision'])
        require(key not in records and kind not in kinds, 'Duplicate artifact or kind in minimal package')
        records[key] = artifact
        kinds[kind] = artifact['data']
    require(set(kinds) == {'script','video-script','assets','scene','audio','alignment','timeline','output-profile'}, 'Incomplete package')

    def resolve(value):
        if isinstance(value, dict):
            if set(value) == {'artifact_id', 'revision'}:
                require((value['artifact_id'], value['revision']) in records, 'Dangling artifact reference')
            for child in value.values():
                resolve(child)
        elif isinstance(value, list):
            for child in value:
                resolve(child)
    resolve(list(kinds.values()))
    for kind, data in kinds.items():
        for field in ('script', 'assets', 'output-profile', 'video-script', 'audio', 'alignment', 'scene'):
            if field in data:
                target = data[field]
                require(records[(target['artifact_id'], target['revision'])]['kind'] == field, 'Reference kind mismatch')

    def unique(items):
        ids = [item['id'] for item in items]
        require(len(ids) == len(set(ids)), 'Duplicate object ID')
        return {item['id']: item for item in items}

    paragraphs = unique(kinds['script']['paragraphs'])
    scenes = unique(kinds['video-script']['scenes'])
    assets = unique(kinds['assets']['items'])
    scene_items = unique(kinds['scene']['items'])
    require(set(scenes) == set(scene_items), 'Scene package does not match storyboard')
    for scene in scenes.values():
        require(all(pid in paragraphs for pid in scene['paragraph_ids']), 'Unknown paragraph')
        require(all(aid in assets for aid in scene['asset_ids']), 'Unknown asset')
        unique(scene['events'])
        for event in scene['events']:
            require(event['target_id'] in scene_items[scene['id']]['element_ids'], 'Unknown animation target')
        for anchor in [scene['start_anchor'], scene['end_anchor']] + [event['anchor'] for event in scene['events']]:
            require(anchor['paragraph_id'] in scene['paragraph_ids'], 'Anchor outside scene paragraphs')
            if 'text_range' in anchor:
                span=anchor['text_range']
                require(0<=span['start']<span['end']<=len(paragraphs[anchor['paragraph_id']][kinds['alignment'].get('span_basis','spoken_text')]), 'Anchor range outside paragraph')
    for scene in scene_items.values():
        require(all(aid in assets for aid in scene['asset_ids']), 'Unknown scene asset')
        require(scene['status'] != 'ready' or bool(scene['entry']), 'Ready scene has no entry')

    def local_file(name):
        path = (directory / name).resolve()
        require(not Path(name).is_absolute() and path.is_relative_to(directory) and path.is_file(), 'Unavailable local resource')
        return path
    for asset in assets.values():
        require(hashlib.sha256(local_file(asset['path']).read_bytes()).hexdigest() == asset['sha256'], 'Asset hash mismatch')
    for scene in scene_items.values():
        if scene['entry']:
            local_file(scene['entry'])
    audio = kinds['audio']
    require(not audio['media_available'] or bool(audio['media_path']), 'Available audio needs path')
    if audio['media_path']:
        local_file(audio['media_path'])
    unique(audio['segments'])
    previous = 0
    for segment in audio['segments']:
        require(previous <= segment['start_sample'] < segment['end_sample'] <= audio['total_samples'], 'Invalid audio range')
        previous = segment['end_sample']
        text = ''
        for span in segment['script_spans']:
            require(span['paragraph_id'] in paragraphs, 'Unknown text span paragraph')
            spoken = paragraphs[span['paragraph_id']]['spoken_text']
            require(0 <= span['start'] < span['end'] <= len(spoken), 'Invalid Unicode codepoint span')
            text += spoken[span['start']:span['end']]
        require(text == segment['spoken_text'], 'Audio text mapping differs from actual spoken text')
    alignment = kinds['alignment']
    units = unique(alignment['units'])
    unique(alignment['cues'])
    for items in (alignment['units'], alignment['cues'], kinds['timeline']['scenes']):
        previous = 0
        for item in items:
            require(previous <= item['start_sample'] < item['end_sample'] <= audio['total_samples'], 'Invalid time ordering or range')
            previous = item['end_sample']
    for unit in units.values():
        span = unit['script_span']
        basis = alignment.get('span_basis','spoken_text')
        require(span['paragraph_id'] in paragraphs and 0 <= span['start'] < span['end'] <= len(paragraphs[span['paragraph_id']][basis]), 'Invalid alignment span')
    for cue in alignment['cues']:
        require(bool(cue['unit_ids']) and all(uid in units for uid in cue['unit_ids']), 'Invalid cue units')
    timeline = kinds['timeline']
    require(timeline['sample_rate'] == audio['sample_rate'] and timeline['duration_samples'] == audio['total_samples'], 'Timeline/audio timebase mismatch')
    if alignment['state'] == 'ready':
        require(bool(units) and bool(alignment['cues']), 'Ready alignment is empty')
    if timeline['state'] == 'ready':
        require(audio['media_available'] and (alignment['state'] == 'ready' or timeline.get('alignment_review_accepted',False)) and bool(timeline['scenes']) and not timeline['blockers'], 'Timeline is not render-ready')
        require(all(s['status'] == 'ready' for s in scene_items.values()), 'Unbuilt scenes')
    for scene in timeline['scenes']:
        require(scene['scene_id'] in scenes, 'Unknown timeline scene')
        for event in scene.get('events',[]):
            require(scene['start_sample']<=event['at_sample']<scene['end_sample'], 'Timeline event outside scene')
    avatar = kinds['output-profile']['avatar']
    require(avatar['x'] + avatar['width'] <= 1 and avatar['y'] + avatar['height'] <= 1, 'Avatar exceeds canvas')
    return dict(status='valid', artifacts=len(records), render_ready=timeline['state'] == 'ready', blockers=timeline['blockers'])


KINDS={'script','video-script','assets','scene','audio','alignment','timeline','output-profile'}


def validate_artifact(artifact):
    kind=artifact['kind']
    require(kind in KINDS,'Unknown artifact kind')
    schema=json.loads((SCHEMAS/(kind+'.schema.json')).read_text(encoding='utf-8'))
    Draft202012Validator(schema).validate(artifact)


def local_resource(directory,name):
    directory=Path(directory).resolve()
    path=(directory/name).resolve()
    require(not Path(name).is_absolute() and path.is_relative_to(directory) and path.is_file(),'Unavailable local resource: '+str(name))
    return path


def load_records(directory):
    directory=Path(directory).resolve()
    index=json.loads((directory/'package.json').read_text(encoding='utf-8'))
    require(index['schema_version']=='0.1.0','Unsupported package version')
    records={}
    for item in index['artifacts']:
        path=local_resource(directory,item['path'])
        require(hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],'Artifact hash mismatch; explicitly re-index reviewed edits')
        artifact=json.loads(path.read_text(encoding='utf-8'))
        validate_artifact(artifact)
        require(artifact['kind'] not in records,'Duplicate artifact kind')
        records[artifact['kind']]=artifact
    require(len({(a['artifact_id'],a['revision']) for a in records.values()})==len(records),'Duplicate artifact identity')
    return records


def index_artifacts(directory):
    directory=Path(directory).resolve()
    artifacts=[]
    for kind in sorted(KINDS):
        path=directory/(kind+'.json')
        if path.exists():
            artifact=json.loads(local_resource(directory,path.name).read_text(encoding='utf-8'))
            validate_artifact(artifact)
            require(artifact['kind']==kind,'Canonical artifact filename has wrong kind')
            artifacts.append(dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    require(bool(artifacts),'No canonical artifacts to index')
    from .common import write_json
    write_json(directory/'package.json',dict(schema_version='0.1.0',artifacts=artifacts))
    return dict(status='ready',artifacts=len(artifacts),index=str(directory/'package.json'))


def validate_partial(directory,phase='storyboard'):
    directory=Path(directory).resolve()
    records=load_records(directory)
    needed={'script','video-script','assets','output-profile'}
    if phase=='scenes':
        needed.add('scene')
    require(needed<=set(records),'Missing authoring inputs: '+', '.join(sorted(needed-set(records))))
    def ref(value,kind):
        require(value=={k:records[kind][k] for k in ('artifact_id','revision')},'Stale '+kind+' reference')
    story=records['video-script']['data'];script=records['script']['data']
    for key in ('script','assets','output-profile'):
        ref(story[key],key)
    paragraphs={p['id']:p for p in script['paragraphs']}
    require(len(paragraphs)==len(script['paragraphs']) and bool(paragraphs),'Paragraph IDs must be unique and nonempty')
    scenes=story['scenes']
    require(bool(scenes) and len({s['id'] for s in scenes})==len(scenes),'Scene IDs must be unique and nonempty')
    assets={a['id']:a for a in records['assets']['data']['items']}
    require(len(assets)==len(records['assets']['data']['items']),'Duplicate asset ID')
    for asset in assets.values():
        require(hashlib.sha256(local_resource(directory,asset['path']).read_bytes()).hexdigest()==asset['sha256'],'Asset hash mismatch')
    for scene in scenes:
        require(bool(scene['paragraph_ids']) and all(pid in paragraphs for pid in scene['paragraph_ids']),'Unknown scene paragraph')
        require(all(aid in assets for aid in scene['asset_ids']),'Unknown scene asset')
        require(len({e['id'] for e in scene['events']})==len(scene['events']),'Duplicate scene event ID')
        for anchor in [scene['start_anchor'],scene['end_anchor']]+[e['anchor'] for e in scene['events']]:
            require(anchor['paragraph_id'] in scene['paragraph_ids'],'Animation anchor is outside scene paragraphs')
            if 'text_range' in anchor:
                span=anchor['text_range']
                require(0<=span['start']<span['end']<=len(paragraphs[anchor['paragraph_id']]['display_text']),'Anchor text range exceeds display text')
    profile=records['output-profile']['data']
    avatar=profile['avatar']
    require(avatar['x']+avatar['width']<=1 and avatar['y']+avatar['height']<=1,'Avatar exceeds canvas')
    if phase=='scenes':
        manifest=records['scene']['data'];ref(manifest['video-script'],'video-script')
        items={s['id']:s for s in manifest['items']}
        require(set(items)=={s['id'] for s in scenes} and len(items)==len(manifest['items']),'HTML scene IDs do not match storyboard')
        mode='portrait' if profile['height']>=profile['width'] else 'landscape'
        for scene in scenes:
            item=items[scene['id']]
            require(item['status']=='ready' and bool(item['entry']),'HTML scene is not built')
            local_resource(directory,item['entry'])
            require(mode in item['layout_modes'],'Scene does not support selected aspect ratio')
            require(all(e['target_id'] in item['element_ids'] for e in scene['events']),'Unknown HTML animation target')
            require(all(aid in assets for aid in item['asset_ids']),'Unknown HTML asset')
    return dict(status='ready',phase=phase,scenes=len(scenes),render_ready=False,
                next_required=[k for k in ('audio','alignment') if k not in records],review_required=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.package), ensure_ascii=False))
