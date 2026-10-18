#!/usr/bin/env python3
"""Stable local CLI for agents. stdout JSON, stderr diagnostics."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

from castlib.common import CastError, item_path, read_json, result, root_path
from castlib.setup import FEATURES, doctor, setup
from castlib.voice import confirm_voice, create_voice, export_job, list_voices, load_job, generate, run_job


def task_video(args):
    path = getattr(args, 'video_config_file', None)
    if not path:
        return None
    value = read_json(path)
    if not isinstance(value, dict):
        raise CastError('invalid_video_config', 'Video preference files must contain a JSON object.')
    return value


def dispatch(args, root):
    if args.command == 'assets':
        from castlib import assets
        if args.action == 'build':
            return assets.build(args.manifest_file, args.output, args.previous)
        if args.action == 'attach':
            return assets.attach(args.assets_file, args.package)
        return assets.validate(args.assets_file)
    if args.command == 'config':
        from castlib.config import resolve
        from castlib.video_config import resolve_video
        return dict(status='ready', **resolve(args.directory, args.language, root), **resolve_video(args.directory, task_video(args), root))
    if args.command == 'batch':
        from castlib import batch
        if args.action=='create':
            return batch.create(args.directory,args.name,args.brief_file)
        if args.action=='add':
            return batch.add(args.directory,args.project,args.topic,args.name,args.target,args.force,args.brief_file)
        if args.action=='status':
            return batch.status(args.directory)
        if args.action=='next':
            return batch.next_item(args.directory)
        if args.action=='report':
            return batch.report(args.directory,args.output,args.language,root)
        return batch.control(args.directory,args.action,getattr(args,'item',None),getattr(args,'message',None),getattr(args,'needs_input',False),getattr(args,'worker_stopped',False))
    if args.command == 'produce':
        from castlib import produce
        if args.action=='plan':
            return produce.plan(args.directory,args.target,args.topic,args.force,args.language,task_video(args))
        if args.action=='status':
            return produce.status(args.directory,args.run)
        if args.action=='assemble':
            from castlib.media import author
            return author(root,'produce-assemble',directory=str(Path(args.directory or '.').resolve()),run_id=args.run,output=args.output)
        return produce.update(args.directory,args.run,args.stage,args.action,
                              version=getattr(args,'version',None),job_id=getattr(args,'job',None),
                              message=getattr(args,'message',None),needs_input=getattr(args,'needs_input',False))
    if args.command == 'script':
        from castlib.config import check_artifact_language
        check_artifact_language(read_json(args.script_file), args.output if args.action=='export' else args.script_file, args.language, root)
        from castlib.media import author
        options=dict(script_file=args.script_file,source_file=args.source_file,target_seconds=args.target_seconds,characters_per_second=args.characters_per_second)
        if args.action=='export':
            options['output']=args.output
        return author(root,'script-'+args.action,**options)
    if args.command == 'project' and args.action != 'index':
        from castlib import project
        if args.action == 'init':
            return project.initialize(args.directory, args.name)
        if args.action == 'status':
            return project.inspect_project(args.directory)
        if args.action == 'path':
            return project.next_path(args.directory, args.stage)
        if args.action == 'register':
            return project.register(args.directory, args.stage, args.version, args.depends_on, args.state)
        return project.select(args.directory, args.stage, args.version)
    if args.command == 'research':
        from castlib.config import check_artifact_language
        check_artifact_language(read_json(args.report_file), args.output if args.action=='export' else args.report_file, args.language, root)
        from castlib.media import author
        options=dict(report_file=args.report_file)
        if args.action=='export':
            options['output']=args.output
        return author(root,'research-'+args.action,**options)
    if args.command == 'doctor':
        return doctor(root, args.feature)
    if args.command == 'setup':
        from castlib.config import configure
        configured = configure(args.directory, args.output_language, root, task_video(args))
        if not args.feature:
            return configured
        response = setup(root, args.feature)
        response['configuration'] = configured
        return response
    if args.command == 'voice':
        if args.action == 'list':
            return result(voices=list_voices(root))
        if args.action == 'confirm':
            return confirm_voice(root, args.id, args.reference_text)
        return create_voice(root, args.audio, args.reference_text, args.name, args.language)
    if args.command == 'speech':
        if args.action == 'generate':
            text = args.text if args.text is not None else Path(args.text_file).read_text(encoding='utf-8-sig') if args.text_file else None
            return generate(root, text, args.voice, args.speed, args.output,script_file=args.script_file, language=args.language)
        if args.action == 'resume':
            return run_job(root, args.job, output=args.output)
        if args.action == 'retry':
            return run_job(root, args.job, retry=args.segment, replacement=args.text, output=args.output)
        if args.action == 'export':
            return export_job(root, load_job(root, args.job), args.output)
    if args.command == 'task':
        job = load_job(root, args.job)
        if args.action == 'cancel':
            if job['status'] not in ('running', 'pending'):
                return result(job_id=args.job, message='Task is not running; nothing to cancel.')
            (item_path(root, 'jobs', args.job) / 'cancel').touch()
            return result('cancelling', job_id=args.job)
        return result(job=job)
    if args.command in ('project','storyboard','scenes','video'):
        from castlib.media import author,render
        if args.command=='project':
            return author(root,'index',package=args.package)
        if args.command=='storyboard' and args.action=='prepare':
            return author(root,'prepare',text_file=args.text_file,script_file=args.script_file,profile_file=args.profile_file,output=args.output,language=args.language,video_config=task_video(args))
        if args.action=='validate':
            return author(root,'validate',package=args.package,phase=args.command)
        if args.action=='compile':
            return author(root,'compile',package=args.package,output=args.output,accept_alignment=args.accept_reviewed_alignment)
        return render(root,args.package,args.output,check_only=args.action=='check',scene_preview=args.command=='scenes')
    if args.command == 'subtitles':
        from castlib.subtitles import generate as generate_subtitles
        return generate_subtitles(root,args.job,args.audio,args.text_file,args.spoken_text_file,args.output,language=args.language)


def main():
    parser = argparse.ArgumentParser(description='codoop-cast local runtime')
    parser.add_argument('--root', help='Private data directory; alternatively CODOOP_CAST_HOME')
    commands = parser.add_subparsers(dest='command', required=True)
    asset_commands = commands.add_parser('assets').add_subparsers(dest='action', required=True)
    asset_build = asset_commands.add_parser('build')
    asset_build.add_argument('--manifest-file', required=True)
    asset_build.add_argument('--output', required=True)
    asset_build.add_argument('--previous')
    for action in ('validate', 'attach'):
        child = asset_commands.add_parser(action)
        child.add_argument('--assets-file', required=True)
        if action == 'attach':
            child.add_argument('--package', required=True)
    doctor_parser = commands.add_parser('doctor')
    doctor_parser.add_argument('--feature', choices=list(FEATURES))
    install = commands.add_parser('setup')
    install.add_argument('--feature', choices=list(FEATURES))
    install.add_argument('--directory', help='Optional project or collection configuration scope')
    install.add_argument('--output-language', help='Artifact language: auto or a BCP 47 tag')
    install.add_argument('--video-config-file', help='JSON video preference patch to save')
    config_parser = commands.add_parser('config')
    config_parser.add_argument('action', choices=['show'])
    config_parser.add_argument('--directory')
    config_parser.add_argument('--language', help='Resolve a current-task override without saving it')
    config_parser.add_argument('--video-config-file', help='Resolve a video patch without saving it')
    voices = commands.add_parser('voice').add_subparsers(dest='action', required=True)
    voices.add_parser('list')
    create = voices.add_parser('create')
    create.add_argument('--audio', required=True)
    create.add_argument('--reference-text')
    create.add_argument('--name')
    create.add_argument('--language', choices=['zh', 'en'], default='zh')
    confirm = voices.add_parser('confirm')
    confirm.add_argument('--id', required=True)
    confirm.add_argument('--reference-text', required=True)
    speech = commands.add_parser('speech').add_subparsers(dest='action', required=True)
    gen = speech.add_parser('generate')
    text = gen.add_mutually_exclusive_group(required=True)
    text.add_argument('--text')
    text.add_argument('--text-file')
    text.add_argument('--script-file')
    gen.add_argument('--voice')
    gen.add_argument('--language', help='Plain-text task language; structured scripts pin their own language')
    gen.add_argument('--speed', type=float, default=1.0)
    gen.add_argument('--output')
    for action in ('resume', 'retry', 'export'):
        command = speech.add_parser(action)
        command.add_argument('--job', required=True)
        command.add_argument('--output')
        if action == 'retry':
            command.add_argument('--segment', type=int, required=True)
            command.add_argument('--text')
    tasks = commands.add_parser('task').add_subparsers(dest='action', required=True)
    for action in ('status', 'cancel'):
        command = tasks.add_parser(action)
        command.add_argument('--job', required=True)
    subtitles=commands.add_parser('subtitles').add_subparsers(dest='action',required=True)
    subgen=subtitles.add_parser('generate')
    subinput=subgen.add_mutually_exclusive_group(required=True)
    subinput.add_argument('--job')
    subinput.add_argument('--audio')
    subgen.add_argument('--text-file')
    subgen.add_argument('--language', help='Language of an external transcript; speech jobs pin their own language')
    subgen.add_argument('--spoken-text-file')
    subgen.add_argument('--output',help='New directory for subtitle artifacts')
    for group,actions in {'project':['index'],'storyboard':['prepare','validate'],'scenes':['validate','check'],'video':['compile','check','render']}.items():
        children=commands.add_parser(group).add_subparsers(dest='action',required=True)
        if group=='project':
            from castlib.project import STAGES
            for operation in ('init','status','path','register','select'):
                command=children.add_parser(operation)
                command.add_argument('--directory',required=operation=='init',default=None)
                if operation=='init':
                    command.add_argument('--name')
                if operation in ('path','register','select'):
                    command.add_argument('--stage',choices=list(STAGES),required=True)
                if operation in ('register','select'):
                    command.add_argument('--version',required=True)
                if operation=='register':
                    command.add_argument('--depends-on',action='append',default=[])
                    command.add_argument('--state',choices=['ready','partial'],default='ready')
        for action in actions:
            child=children.add_parser(action)
            if action=='prepare':
                source=child.add_mutually_exclusive_group(required=True)
                source.add_argument('--text-file');source.add_argument('--script-file')
                child.add_argument('--language', help='Concrete language of an imported plain-text script')
                settings = child.add_mutually_exclusive_group()
                settings.add_argument('--profile-file')
                settings.add_argument('--video-config-file', help='Task video preference patch')
            else:
                child.add_argument('--package',required=True)
            if action in ('prepare','compile','check','render'):
                child.add_argument('--output',required=True)
            if action=='compile':
                child.add_argument('--accept-reviewed-alignment',action='store_true')
    research=commands.add_parser('research').add_subparsers(dest='action',required=True)
    for action in ('validate','export'):
        child=research.add_parser(action)
        child.add_argument('--report-file',required=True)
        child.add_argument('--language', help='Current-task target language override')
        if action=='export':
            child.add_argument('--output',required=True)
    scripting=commands.add_parser('script').add_subparsers(dest='action',required=True)
    for action in ('validate','export'):
        child=scripting.add_parser(action)
        child.add_argument('--script-file',required=True)
        child.add_argument('--language', help='Current-task target language override')
        child.add_argument('--source-file',required=action=='export')
        child.add_argument('--target-seconds',type=float)
        child.add_argument('--characters-per-second',type=float,default=4.0)
        if action=='export':
            child.add_argument('--output',required=True)
    from castlib.produce import GRAPH
    production=commands.add_parser('produce').add_subparsers(dest='action',required=True)
    for action in ('plan','status','start','checkpoint','fail','assemble'):
        child=production.add_parser(action)
        child.add_argument('--directory')
        if action=='plan':
            child.add_argument('--target',choices=list(GRAPH),default='exports')
            child.add_argument('--language', help='Current-task target language')
            child.add_argument('--video-config-file', help='Task video preference patch')
            child.add_argument('--topic')
            child.add_argument('--force',choices=list(GRAPH),action='append',default=[])
        else:
            child.add_argument('--run',required=True)
        if action in ('start','checkpoint','fail'):
            child.add_argument('--stage',choices=list(GRAPH),required=True)
            child.add_argument('--job')
        if action=='checkpoint':
            child.add_argument('--version',required=True)
        if action=='fail':
            child.add_argument('--message',required=True)
            child.add_argument('--needs-input',action='store_true')
        if action=='assemble':
            child.add_argument('--output')
    batches=commands.add_parser('batch').add_subparsers(dest='action',required=True)
    for action in ('create','add','status','next','pause','resume','cancel','retry','defer','report'):
        child=batches.add_parser(action)
        child.add_argument('--directory',required=True)
        if action in ('create','add'):
            child.add_argument('--name')
            child.add_argument('--brief-file')
        if action=='add':
            child.add_argument('--project')
            child.add_argument('--topic')
            child.add_argument('--target',choices=list(GRAPH),default='exports')
            child.add_argument('--force',choices=list(GRAPH),action='append',default=[])
        if action in ('retry','defer'):
            child.add_argument('--item',required=True)
        if action=='defer':
            child.add_argument('--message',required=True)
            child.add_argument('--needs-input',action='store_true')
            child.add_argument('--worker-stopped',action='store_true')
        if action=='report':
            child.add_argument('--output')
            child.add_argument('--language')
    args = parser.parse_args()
    try:
        selected_root = root_path(args.root)
        os.environ['CODOOP_CAST_HOME'] = str(selected_root)
        data = dispatch(args, selected_root)
        print(json.dumps(data, ensure_ascii=False))
        return 0 if data['status'] in ('ready', 'cancelling') else 2
    except KeyboardInterrupt:
        print(json.dumps(result('interrupted', error={'code': 'interrupted', 'message': 'Task interrupted; inspect task status before resuming.'})))
        return 130
    except Exception as exc:
        code = exc.code if isinstance(exc, CastError) else 'runtime_error'
        print(json.dumps(result('failed', error={'code': code, 'message': str(exc)}, next_action=getattr(exc, 'next_action', None)), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
