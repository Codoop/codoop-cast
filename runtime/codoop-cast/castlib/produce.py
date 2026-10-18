"""Persistent single-project workflow plans; the host agent executes creative skills."""
from pathlib import Path
import time

from .config import resolve, check_artifact_language
from .video_config import resolve_video, profile_data
from .common import CastError, digest, item_path, lock, new_id, read_json, write_json
from .project import checked_record, inspect_project, locate, next_path, select

GRAPH = {'research': [], 'script': ['research'], 'storyboard': ['script'], 'voice': ['script'],
         'subtitles': ['voice'], 'assets': ['storyboard'], 'scenes': ['storyboard', 'assets'], 'exports': ['subtitles', 'scenes']}
SKILLS = {stage: 'codoop-'+{'exports':'video','voice':'voice'}.get(stage,stage) for stage in GRAPH}


def require(value, message):
    if not value:
        raise CastError('invalid_workflow', message)


def verify_export(root, version):
    report=read_json(root/'exports'/version/'video-qa/render.json')
    require(report.get('status')=='rendered' and not report.get('errors')
            and report.get('video_sha256')==digest(root/'exports'/version/'video.mp4'),
            'Final video lacks a matching successful render report.')


def run_files(directory, run_id):
    root, _ = locate(directory)
    folder = item_path(root/'.cast', 'runs', run_id)
    return root, folder, read_json(folder/'plan.json'), read_json(folder/'state.json')


def plan(directory=None, target='exports', topic=None, force=(), language=None, video=None):
    root, project = locate(directory)
    require(target in GRAPH and all(s in GRAPH for s in force), 'Unknown workflow stage.')
    ancestors = set()
    def visit(stage):
        ancestors.add(stage)
        for parent in GRAPH[stage]:
            visit(parent)
    visit(target)
    require(set(force) <= ancestors, 'Forced stages must contribute to the selected target.')
    configuration = resolve(root, language)
    video_settings = resolve_video(root, video) if target in ('storyboard', 'assets', 'scenes', 'exports') else None
    changed = set(force)
    if video_settings and video_settings['video_explicit']:
        expected_profile = profile_data(video_settings['video'])
        for stage in ('storyboard', 'scenes', 'exports'):
            version = project['current'][stage]
            if version:
                path = root/stage/version/('production/output-profile.json' if stage == 'exports' else 'output-profile.json')
                try:
                    matches = read_json(path).get('data') == expected_profile
                except (OSError, ValueError):
                    matches = False
                if not matches:
                    changed.add(stage)
    if configuration['output_language'] != 'auto':
        for stage, filename in (('research', 'report.json'), ('script', 'script.json')):
            version = project['current'][stage]
            if version:
                try:
                    artifact = read_json(root/stage/version/filename)
                except (OSError, ValueError):
                    continue  # Structural checks still own invalid/missing stage files.
                try:
                    check_artifact_language(artifact, root, configuration['output_language'])
                except CastError as exc:
                    if exc.code == 'language_mismatch':
                        changed.add(stage)
                    else:
                        raise
    for stage in GRAPH:
        if any(p in changed for p in GRAPH[stage]):
            changed.add(stage)
    snapshot = inspect_project(root)
    steps = []
    def add(stage):
        if any(s['stage'] == stage for s in steps):
            return
        current = snapshot['stages'][stage]
        if stage=='exports' and current['state']=='ready':
            try:
                verify_export(root,current['version'])
            except (OSError, ValueError, CastError):
                current=dict(current,state='invalid')
        reuse = current['state'] == 'ready' and stage not in changed
        dependencies = [] if reuse else GRAPH[stage]
        for parent in dependencies:
            add(parent)
        action = 'reuse' if reuse else 'review' if current['state'] in ('partial','invalid') and stage not in changed else 'build'
        version = current['version'] if reuse else None
        steps.append(dict(stage=stage, skill=SKILLS[stage], action=action, dependencies=dependencies,
                          selected_state=current['state'], selected_version=current['version'], version=version,
                          manifest_sha256=digest(root/stage/version/'version.json') if reuse else None))
    add(target)
    run_id = new_id()
    folder = root/'.cast/runs'/run_id
    with lock(root/'.cast','produce'):
        folder.mkdir(parents=True)
        record = dict(schema_version='0.1.0', kind='workflow-plan', run_id=run_id, project_id=project['project_id'],
                      target=target, topic=topic, output_language=configuration['output_language'], language_override=language,
                      video=video_settings['video'] if video_settings else None, video_override=video,
                      video_enforced=video_settings['video_explicit'] if video_settings else False,
                      force=list(force), created_at=time.time(), steps=steps)
        state = dict(schema_version='0.1.0', run_id=run_id, plan_sha256=None,
                     steps={s['stage']:dict(state='reused' if s['action']=='reuse' else 'pending', version=s['version'],
                                          manifest_sha256=s['manifest_sha256'], job_id=None, attempts=0) for s in steps}, events=[])
        write_json(folder/'plan.json',record)
        state['plan_sha256']=digest(folder/'plan.json')
        write_json(folder/'state.json',state)
    return status(root,run_id)


def changed_inputs(root, folder, plan, state):
    reasons = []
    _, project = locate(root)
    if 'output_language' in plan and resolve(root, plan.get('language_override'))['output_language'] != plan['output_language']:
        reasons.append('Output language changed; create a new plan.')
    if plan.get('video') is not None and resolve_video(root, plan.get('video_override'))['video'] != plan['video']:
        reasons.append('Video configuration changed; create a new plan.')
    if project['project_id'] != plan['project_id'] or digest(folder/'plan.json') != state['plan_sha256']:
        reasons.append('Project identity or saved plan changed.')
    for stage, entry in state['steps'].items():
        if entry['state'] not in ('reused','succeeded'):
            continue
        try:
            checked_record(root,stage,entry['version'])
            if stage=='exports':
                verify_export(root,entry['version'])
            require(project['current'][stage] == entry['version'], 'Selected version changed: '+stage)
            require(digest(root/stage/entry['version']/'version.json') == entry['manifest_sha256'], 'Version manifest changed: '+stage)
            require(inspect_project(root)['stages'][stage]['state']=='ready', 'Selected dependencies changed: '+stage)
        except (OSError, ValueError, KeyError, CastError) as exc:
            reasons.append(str(exc))
    return reasons


def status(directory, run_id):
    root, folder, record, state = run_files(directory,run_id)
    changes = changed_inputs(root,folder,record,state)
    entries = state['steps']
    complete = all(s['state'] in ('reused','succeeded') for s in entries.values())
    phase = 'needs_replan' if changes else 'complete' if complete else 'needs_input' if any(s['state']=='needs_input' for s in entries.values()) else 'failed' if any(s['state']=='failed' for s in entries.values()) else 'running' if any(s['state']=='running' for s in entries.values()) else 'pending'
    available = []
    for step in record['steps']:
        if entries[step['stage']]['state'] not in ('reused','succeeded','running') and all(entries[p]['state'] in ('reused','succeeded') for p in step['dependencies']):
            available.append(dict(stage=step['stage'],action=step['action'],skill=SKILLS.get(step['stage'], step['skill'])))
    return dict(status='ready',run_id=run_id,workflow_state=phase,output_language=record.get('output_language'),video=record.get('video'),target=record['target'],project=str(root),
                plan=str(folder/'plan.json'),state=str(folder/'state.json'),steps=entries,
                next_steps=available if not changes else [],changed_inputs=changes,
                note='The host agent executes skills; recorded progress is not approval or factual verification.')


def update(directory, run_id, stage, operation, version=None, job_id=None, message=None, needs_input=False):
    root, folder, _, _ = run_files(directory,run_id)
    with lock(root/'.cast','produce'):
        root, folder, record, state = run_files(root,run_id)
        if operation!='fail':
            require(not changed_inputs(root,folder,record,state), 'Workflow inputs changed; create a new plan before continuing.')
        step = next((s for s in record['steps'] if s['stage']==stage),None)
        require(step is not None, 'Stage is not in this plan.')
        entry = state['steps'][stage]
        require(entry['state'] not in ('reused','succeeded'), 'Completed stages are immutable; create a new plan/version.')
        require(all(state['steps'][p]['state'] in ('reused','succeeded') for p in step['dependencies']), 'Complete required upstream steps first.')
        if operation=='start':
            require(entry['state'] != 'running', 'Stage already started; inspect its recorded task before retrying.')
            entry.update(state='running',attempts=entry['attempts']+1,job_id=job_id,message=None)
            entry['output_candidate']=next_path(root,stage)['output']
        elif operation=='checkpoint':
            require(entry['state']=='running', 'Start the stage before recording completion.')
            require(version!=step.get('selected_version'), 'Rebuilding requires a new version, not the previous selection.')
            registered=checked_record(root,stage,version)
            require(registered['state']=='ready', 'Partial output cannot silently satisfy a workflow step.')
            if stage in ('research', 'script') and record.get('output_language', 'auto') != 'auto':
                filename = 'report.json' if stage == 'research' else 'script.json'
                check_artifact_language(read_json(root/stage/version/filename), root, record['output_language'])
            if stage in ('storyboard', 'scenes', 'exports') and record.get('video_enforced'):
                profile = root/stage/version/('production/output-profile.json' if stage == 'exports' else 'output-profile.json')
                require(profile.is_file() and read_json(profile).get('data') == profile_data(record['video']),
                        'Output profile differs from the planned video configuration; prepare a matching new version.')
            actual={d['stage']:d for d in registered['dependencies']}
            for parent in step['dependencies']:
                expected=state['steps'][parent]
                require(parent in actual and actual[parent]['version']==expected['version']
                        and actual[parent]['sha256']==expected['manifest_sha256'], 'Registered dependencies differ from this plan: '+parent)
            if stage=='exports':
                verify_export(root,version)
            select(root,stage,version)
            entry.update(state='succeeded',version=version,manifest_sha256=digest(root/stage/version/'version.json'),
                         job_id=job_id or entry['job_id'],message=None)
        else:
            require(operation=='fail' and entry['state']=='running' and bool(message), 'Record a concrete failure for a running stage.')
            entry.update(state='needs_input' if needs_input else 'failed',message=message,job_id=job_id or entry['job_id'])
        state['events'].append(dict(stage=stage,operation=operation,at=time.time(),version=version,job_id=entry['job_id'],message=message))
        write_json(folder/'state.json',state)
    return status(root,run_id)
