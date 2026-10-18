"""Schema-aware, lightweight authoring operations in a private interpreter."""
import argparse
import hashlib
from pathlib import Path
import shutil

from castlib.common import read_json,write_json,new_id
from castlib.contracts import index_artifacts,load_records,local_resource,validate_artifact,validate_partial,validate
from castlib.timeline import compile_timeline,reference


def prepare(request):
    output=Path(request['output'])
    if output.exists():
        raise ValueError('Use a new authoring output directory.')
    if request.get('script_file'):
        script=read_json(request['script_file'])
        validate_artifact(script)
        if script['kind']!='script':
            raise ValueError('Expected a script artifact.')
    else:
        from castlib.config import resolve
        language = resolve(output, request.get('language'), request.get('data_root'))['output_language']
        if language == 'auto':
            raise ValueError('Resolve the imported transcript language and pass --language before preparing a storyboard.')
        text=Path(request['text_file']).read_text(encoding='utf-8-sig').strip()
        blocks=[line.strip() for line in text.splitlines() if line.strip()]
        if not blocks or not any(c.isalnum() for c in text):
            raise ValueError('Provide a nonempty narration script.')
        seen={};paragraphs=[]
        for block in blocks:
            key=hashlib.sha256(block.encode()).hexdigest()[:12]
            seen[key]=seen.get(key,0)+1
            paragraphs.append(dict(id='p-'+key+'-'+str(seen[key]),display_text=block,spoken_text=block,claim_ids=[]))
        script=dict(schema_version='0.1.0',kind='script',artifact_id=new_id(),revision=1,
                    data=dict(language=language,provenance='Imported user narration; no research provenance inferred.',paragraphs=paragraphs))
    from castlib.video_config import resolve_video, profile_data
    profile=read_json(request['profile_file']) if request.get('profile_file') else dict(
        schema_version='0.1.0',kind='output-profile',artifact_id=new_id(),revision=1,
        data=profile_data(resolve_video(output, request.get('video_config'), request.get('data_root'))['video']))
    validate_artifact(profile)
    if profile['kind']!='output-profile':
        raise ValueError('Expected an output-profile artifact.')
    assets=dict(schema_version='0.1.0',kind='assets',artifact_id=new_id(),revision=1,data=dict(items=[]))
    output.mkdir(parents=True)
    for kind,artifact in [('script',script),('output-profile',profile),('assets',assets)]:
        write_json(output/(kind+'.json'),artifact)
    (output/'script.txt').write_text('\n\n'.join(p['display_text'] for p in script['data']['paragraphs']),encoding='utf-8')
    index_artifacts(output)
    return dict(status='ready',package=str(output),phase='inputs_prepared',storyboard_created=False,
                next_action='Author video-script.json from this narration, then explicitly index and validate the plan.')


def compile_project(request):
    source=Path(request['package']).resolve();output=Path(request['output']).resolve()
    if output.exists() or output.is_relative_to(source):
        raise ValueError('Compile to a new directory outside the input package.')
    validate_partial(source,'scenes')
    records=load_records(source)
    if not {'audio','alignment'}<=set(records):
        raise ValueError('Precise video timing requires actual audio and alignment artifacts.')
    if records['alignment']['data'].get('span_basis','spoken_text')!='display_text':
        if any(p['display_text']!=p['spoken_text'] for p in records['script']['data']['paragraphs']):
            raise ValueError('Storyboard anchors require display-text alignment when display and spoken forms differ.')
    timeline=compile_timeline(records['script'],records['video-script'],records['audio'],records['alignment'],
        records['scene'],records['output-profile'],accept_reviewed_alignment=request.get('accept_alignment',False))
    files={entry['path'] for entry in read_json(source/'package.json')['artifacts']}
    files.update(a['path'] for a in records['assets']['data']['items'])
    files.update(s['entry'] for s in records['scene']['data']['items'])
    if not records['audio']['data']['media_available']:
        raise ValueError('The source package has no actual local audio.')
    files.add(records['audio']['data']['media_path'])
    files.update(name for name in ('visuals.json','checks.json','review.json','subtitles.srt','storyboard.md','script.txt') if (source/name).is_file())
    for name in files:
        local_resource(source,name)
    output.mkdir(parents=True)
    for name in sorted(files):
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(local_resource(source,name),target)
    write_json(output/'timeline.json',timeline)
    index_artifacts(output)
    validated=validate(output)
    return dict(status='ready',package=str(output),render_ready=validated['render_ready'],timeline=str(output/'timeline.json'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--response',type=Path,required=True)
    args=parser.parse_args()
    request=read_json(args.request)
    try:
        operation=request['operation']
        if operation=='produce-assemble':
            from castlib.assembly import assemble
            response=assemble(request['directory'],request['run_id'],request.get('output'))
        elif operation in ('script-validate','script-export'):
            from castlib.script import validate_script,export_script
            options=dict(target_seconds=request.get('target_seconds'),characters_per_second=request.get('characters_per_second',4.0))
            response=validate_script(request['script_file'],request.get('source_file'),**options) if operation=='script-validate' else export_script(request['script_file'],request['source_file'],request['output'],**options)
        elif operation in ('research-validate','research-export'):
            from castlib.research import validate_report,export_report
            response=validate_report(request['report_file']) if operation=='research-validate' else export_report(request['report_file'],request['output'])
        elif operation=='prepare':
            response=prepare(request)
        elif operation=='index':
            response=index_artifacts(request['package'])
        elif operation=='compile':
            response=compile_project(request)
        elif operation=='validate':
            response=validate_partial(request['package'],request.get('phase','storyboard'))
        else:
            raise ValueError('Unknown authoring operation.')
    except Exception as exc:
        response=dict(status='failed',error=dict(code=getattr(exc,'code','invalid_authoring_input'),message=str(exc)))
    write_json(args.response,response)


if __name__=='__main__':
    main()
