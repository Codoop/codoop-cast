"""Persistent sequential project queue, driven by the host agent rather than a daemon."""
import os
import re
from pathlib import Path
import time
from urllib.parse import quote

from .common import CastError, lock, new_id, read_json, write_json
from . import produce, project

MARKER = 'cast-batch.json'


def require(value, message):
    if not value:
        raise CastError('invalid_batch', message)


def load(directory):
    root = Path(directory).expanduser().resolve()
    data = read_json(root / MARKER)
    require(data.get('kind') == 'cast-batch' and data.get('schema_version') == '0.1.0', 'Unsupported batch format.')
    require(len({i['id'] for i in data['items']}) == len(data['items']), 'Duplicate queue item ID.')
    require(data['mode'] in ('active','paused','cancelled'), 'Invalid batch mode.')
    require(sum(i['state']=='active' for i in data['items']) <= 1, 'Only one project may be active.')
    return root, data


def create(directory, name=None, brief_file=None):
    root=Path(directory).expanduser().resolve()
    brief=Path(brief_file).read_text(encoding='utf-8-sig') if brief_file else ''
    require(not any((p/project.MARKER).exists() for p in (root,*root.parents)), 'Use a collection folder outside individual content projects.')
    root.mkdir(parents=True,exist_ok=True)
    with lock(root/'.cast','batch'):
        require(not (root/MARKER).exists(), 'Batch already exists; use status/add to continue.')
        write_json(root/MARKER,dict(schema_version='0.1.0',kind='cast-batch',batch_id=new_id(),name=name or root.name,brief=brief,
                                  mode='active',items=[],events=[]))
    return status(root)


def event(data, action, item=None, message=None):
    data['events'].append(dict(action=action,item_id=item['id'] if item else None,at=time.time(),message=message))


def item_project(root, item):
    path, record=project.locate(root/item['project_path'])
    require(path == (root/item['project_path']).resolve(), 'Queue entry must identify the project root.')
    require(record['project_id'] == item['project_id'], 'Queued project identity changed.')
    return path


def completed(data, item, run):
    if item['state']!='succeeded':
        event(data,'completed',item)
    item.update(state='succeeded',error=None,workflow_state='complete')
    item['output']=dict(stage=run['target'],version=run['steps'][run['target']]['version'],
                        path=(Path(item['project_path'])/run['target']/run['steps'][run['target']]['version']).as_posix())


def refresh(root, data):
    for item in data['items']:
        if not item['run_id'] or item['state'] in ('pending','cancelled'):
            continue
        try:
            path=item_project(root,item)
            run=produce.status(path,item['run_id'])
            item['workflow_state']=run['workflow_state']
            running=any(s['state']=='running' for s in run['steps'].values())
            if run['workflow_state']=='complete':
                completed(data,item,run)
            elif run['workflow_state'] in ('failed','needs_input','needs_replan') and not running:
                item['state']=run['workflow_state']
                messages=[s.get('message') for s in run['steps'].values() if s.get('message')]
                item['error']='; '.join(run['changed_inputs']+messages) or run['workflow_state']
                item['output']=None
            elif item['state']=='succeeded':
                item.update(state='needs_replan',error='Previously completed target is no longer current.',output=None)
        except (OSError, ValueError, KeyError, TypeError, CastError) as exc:
            # Do not free an active worker slot when its live state is unknown.
            if item['state']!='active':
                item['state']='needs_replan'
            item.update(error=str(exc),workflow_state='unavailable',output=None)


def summarize(root, data):
    counts={state:sum(i['state']==state for i in data['items']) for state in ('pending','active','succeeded','failed','needs_input','needs_replan','cancelled')}
    phase='paused' if data['mode']=='paused' else 'cancelled' if data['mode']=='cancelled' else 'running' if counts['active'] else 'pending' if counts['pending'] else 'complete' if counts['succeeded']==len(data['items']) else 'needs_attention'
    return dict(status='ready',batch=str(root/MARKER),batch_state=phase,mode=data['mode'],brief=data.get('brief',''),counts=counts,items=data['items'],
                note='Agent-driven sequential queue; no background worker is started by this command.')


def status(directory):
    root,_=load(directory)
    with lock(root/'.cast','batch'):
        root,data=load(root);refresh(root,data);write_json(root/MARKER,data)
    return summarize(root,data)


def add(directory, project_directory=None, topic=None, name=None, target='exports', force=(), brief_file=None):
    root,_=load(directory)
    require(target in produce.GRAPH and all(s in produce.GRAPH for s in force),'Invalid workflow target or forced stage.')
    ancestors=set()
    def visit(stage):
        ancestors.add(stage)
        for parent in produce.GRAPH[stage]:visit(parent)
    visit(target)
    require(set(force)<=ancestors,'Forced stages must contribute to the batch target.')
    require(bool(project_directory) or bool(topic and topic.strip()),'Provide an existing project or a topic for a new one.')
    brief=Path(brief_file).read_text(encoding='utf-8-sig') if brief_file else ''
    with lock(root/'.cast','batch'):
        root,data=load(root)
        require(data['mode']!='cancelled','Resume the cancelled queue explicitly before adding work.')
        ident=new_id()
        if project_directory:
            path,record=project.locate(project_directory)
        else:
            path=root/'projects'/('project-'+ident[:12])
            while path.exists():
                ident=new_id();path=root/'projects'/('project-'+ident[:12])
            project.initialize(path,name or topic)
            _,record=project.locate(path)
        require(all(i['project_id']!=record['project_id'] for i in data['items']),'Project is already queued; retry its existing item instead.')
        try:
            relative=Path(os.path.relpath(path,root)).as_posix()
        except ValueError:  # Explicitly referenced projects on another Windows volume.
            relative=path.as_posix()
        item=dict(id=ident,project_path=relative,project_id=record['project_id'],name=name or record['name'],topic=topic,brief=brief,
                  target=target,force=list(force),state='pending',run_id=None,run_history=[],attempts=0,error=None,
                  workflow_state=None,output=None)
        data['items'].append(item);event(data,'added',item);write_json(root/MARKER,data)
    return dict(status='ready',item_id=ident,project=str(path),batch=str(root/MARKER))


def next_item(directory):
    root,_=load(directory)
    with lock(root/'.cast','batch'):
        root,data=load(root);refresh(root,data)
        active=next((i for i in data['items'] if i['state']=='active'),None)
        if active:
            write_json(root/MARKER,data)
            return dict(**summarize(root,data),action='continue',active_item=active,
                        cancel_requested=data['mode']=='cancelled')
        if data['mode']!='active':
            write_json(root/MARKER,data)
            return dict(**summarize(root,data),action='idle',active_item=None)
        for item in data['items']:
            if item['state']!='pending':continue
            try:
                path=item_project(root,item)
                old=produce.status(path,item['run_id']) if item['run_id'] else None
                if old is None or old['workflow_state']=='needs_replan':
                    run=produce.plan(path,item['target'],item['topic'],item['force'])
                    item['run_id']=run['run_id'];item['run_history'].append(run['run_id'])
                else:
                    run=old
                item.update(attempts=item['attempts']+1,state='active',error=None,workflow_state=run['workflow_state'])
                event(data,'claimed',item)
                if run['workflow_state']=='complete':
                    completed(data,item,run)
                    continue
                write_json(root/MARKER,data)
                return dict(**summarize(root,data),action='execute',active_item=item,cancel_requested=False)
            except (OSError, ValueError, KeyError, TypeError, CastError) as exc:
                item.update(state='failed',error=str(exc));event(data,'failed',item,str(exc))
        write_json(root/MARKER,data)
        return dict(**summarize(root,data),action='idle',active_item=None)


def control(directory, action, item_id=None, message=None, needs_input=False, worker_stopped=False):
    root,_=load(directory)
    with lock(root/'.cast','batch'):
        root,data=load(root);refresh(root,data)
        item=next((i for i in data['items'] if i['id']==item_id),None) if item_id else None
        if action in ('pause','resume','cancel'):
            data['mode']={'pause':'paused','resume':'active','cancel':'cancelled'}[action]
            if action=='cancel':
                for entry in data['items']:
                    if entry['state']=='pending':entry['state']='cancelled'
            event(data,action)
        else:
            require(item is not None,'Unknown batch item.')
            if action=='retry':
                require(item['state'] in ('failed','needs_input','needs_replan','cancelled'),'Only an unresolved/cancelled item can be retried.')
                if item['run_id']:
                    run=produce.status(item_project(root,item),item['run_id'])
                    require(not any(s['state']=='running' for s in run['steps'].values()),'Reconcile the existing worker before retrying.')
                item.update(state='pending',error=None,output=None)
            else:
                require(action=='defer' and item['state']=='active' and bool(message and message.strip()),'Defer an active item with its concrete cause.')
                try:
                    path=item_project(root,item)
                    run=produce.status(path,item['run_id'])
                except (OSError,ValueError,KeyError,TypeError,CastError):
                    require(worker_stopped,'Worker state is unavailable. Verify the actual task has stopped before using --worker-stopped to release this slot.')
                    item['worker_stopped_asserted']=True
                else:
                    require(not any(s['state']=='running' for s in run['steps'].values()),'Record/cancel the running workflow stage before releasing the queue slot.')
                item.update(state='needs_input' if needs_input else 'failed',error=message,output=None)
            event(data,action,item,message)
        write_json(root/MARKER,data)
    return summarize(root,data)


def report(directory, output=None, language=None, data_root=None):
    from .config import resolve
    from .locale import labels as export_labels
    config = resolve(directory, language, data_root)
    language = 'zh' if config['source'] == 'default' else config['output_language']
    t = export_labels(language, directory)
    summary=status(directory)
    root=Path(summary['batch']).parent
    with lock(root/'.cast','batch'):
        if output:
            target=Path(output).expanduser().resolve()
        else:
            parent=root/'reports'
            versions=[project.version_number(p.name) for p in parent.iterdir() if re.fullmatch(r'v[0-9]{3,}',p.name)] if parent.exists() else []
            target=parent/f'v{max(versions,default=0)+1:03d}'/'batch-report.md'
        require(not target.exists(),'Use a new batch report path; previous reports are preserved.')
        labels={state:t(state) for state in ('pending','active','succeeded','failed','needs_input','needs_replan','cancelled')}
        readable=dict(research='report.md',script='script.md',storyboard='storyboard.md',assets='assets.json',voice='narration.wav',subtitles='subtitles.srt',scenes='scene.json',exports='video.mp4')
        clean=lambda text:str(text or '').replace('|','\\|').replace('\n',' ').replace('\r',' ')
        lines=['# ' + t('Batch production report'),t('Completed {done} / {total} projects; batch state: {state}.').format(done=summary['counts']['succeeded'], total=len(summary['items']), state=t(summary['batch_state'])),
               t('| Project | Status | Artifact | Notes |'),'| --- | --- | --- | --- |']
        for item in summary['items']:
            link='—'
            if item['output']:
                artifact=(root/item['output']['path']/readable[item['output']['stage']]).resolve()
                try:
                    relative=Path(os.path.relpath(artifact,target.parent)).as_posix()
                except ValueError:
                    relative=artifact.as_posix()
                link='[' + t('View') + '](<'+quote(relative,safe='/:')+'>)'
            lines.append(f'| {clean(item["name"])} | {labels[item["state"]]} | {link} | {clean(item["error"])} |')
        if summary['mode']=='cancelled' and summary['counts']['active']:
            lines.append(t('The queue was cancelled with active items; inspect and stop their actual tasks.'))
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text('\n\n'.join(lines[:2])+'\n\n'+'\n'.join(lines[2:])+'\n',encoding='utf-8')
    return dict(status='ready',report=str(target),batch_state=summary['batch_state'],counts=summary['counts'])
