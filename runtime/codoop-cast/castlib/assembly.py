"""Assemble pinned scene/subtitle handoffs without modifying registered inputs."""
from pathlib import Path
import shutil

from .common import digest, read_json
from .contracts import index_artifacts, load_records, local_resource, require, validate_artifact, validate_partial
from .produce import changed_inputs, run_files
from .voice import wav_info


def assemble(directory, run_id, output=None):
    root, folder, plan, state = run_files(directory,run_id)
    require(not changed_inputs(root,folder,plan,state), 'Workflow inputs changed; re-plan before assembly.')
    require('exports' in state['steps'] and state['steps']['exports']['state']=='running', 'Start the export step before assembly.')
    sources = {}
    for stage in ('scenes','subtitles'):
        entry=state['steps'].get(stage)
        require(entry and entry['state'] in ('reused','succeeded'), 'Complete the selected '+stage+' first.')
        sources[stage]=root/stage/entry['version']
    scene, subtitles = sources['scenes'], sources['subtitles']
    validate_partial(scene,'scenes')
    records=load_records(scene)
    sub={kind:read_json(local_resource(subtitles,kind+'.json')) for kind in ('script','audio','alignment')}
    for artifact in sub.values():
        validate_artifact(artifact)
    require(records['script']==sub['script'], 'Scene and subtitle packages use different script artifacts.')
    audio=sub['audio']['data']
    require(audio['media_available'], 'No actual local narration is available.')
    media=local_resource(subtitles,audio['media_path'])
    info=wav_info(media)
    require(info['sample_rate']==audio['sample_rate'] and info['samples']==audio['total_samples'], 'Audio samples differ from the selected manifest.')
    if (subtitles/'checks.json').exists():
        checks=read_json(subtitles/'checks.json')
        require(not checks.get('audio_sha256') or checks['audio_sha256']==digest(media), 'Narration differs from the alignment evidence.')
    output=Path(output).resolve() if output else root/'.cast/work'/run_id/'assembly'
    require(not output.exists(), 'Use a new assembly directory.')
    payloads={}
    def add(name, source, relative):
        name=Path(name).as_posix()
        target=(output/name).resolve()
        require(not Path(name).is_absolute() and target.is_relative_to(output), 'Assembly path escapes the output directory.')
        content=local_resource(source,relative)
        require(name not in payloads or digest(payloads[name])==digest(content), 'Conflicting assembly resources: '+name)
        payloads[name]=content
    indexed={read_json(local_resource(scene,e['path']))['kind']:e['path'] for e in read_json(scene/'package.json')['artifacts']}
    for kind in ('script','video-script','assets','scene','output-profile'):
        add(kind+'.json',scene,indexed[kind])
    for kind in ('audio','alignment'):
        add(kind+'.json',subtitles,kind+'.json')
    for item in records['assets']['data']['items']:
        add(item['path'],scene,item['path'])
    for item in records['scene']['data']['items']:
        add(item['entry'],scene,item['entry'])
    add(audio['media_path'],subtitles,audio['media_path'])
    for name in ('subtitles.srt','checks.json','review.json'):
        if (subtitles/name).is_file():
            add(name,subtitles,name)
    for name in ('visuals.json','storyboard.md','script.txt'):
        if (scene/name).is_file():
            add(name,scene,name)
    output.mkdir(parents=True)
    for name, content in payloads.items():
        path=output/name; path.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(content,path)
    index_artifacts(output)
    return dict(status='ready',package=str(output),files=len(payloads),render_ready=False,
                next_action='Compile the actual timeline, check scenes and render through codoop-cast-video.')
