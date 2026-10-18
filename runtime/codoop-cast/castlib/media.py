"""Public stdlib orchestration for independent authoring and video skills."""
from pathlib import Path
import subprocess
import sys
import time

from .common import CastError,item_path,new_id,read_json,write_json
from .setup import RUNTIME,feature_python,environment,setup,tool_check


def call(root,feature,worker,args,kind,request=None):
    if tool_check(root,feature)['status']!='ready':
        setup(root,feature)
    ident=new_id();directory=item_path(root,'jobs',ident)
    directory.mkdir(parents=True)
    response=directory/'response.json'
    record=dict(id=ident,schema_version=1,kind=kind,status='running',created_at=time.time(),artifacts=[])
    write_json(directory/'job.json',record)
    if request is not None:
        write_json(directory/'request.json',request)
        args=['--request',directory/'request.json']
    else:
        args=[*args,'--cancel-file',directory/'cancel']
    log=root/'logs'/(kind+'-'+ident+'.log');log.parent.mkdir(parents=True,exist_ok=True)
    print('Task '+ident+'; log: '+str(log),file=sys.stderr,flush=True)
    try:
        with log.open('ab') as stream:
            proc=subprocess.run([str(feature_python(root,feature)),str(RUNTIME/worker),*map(str,args),'--response',str(response)],
                                env=environment(root),stdout=stream,stderr=stream)
        if (directory/'cancel').exists():
            result=dict(status='cancelled',job_id=ident,artifacts=[])
        elif proc.returncode or not response.exists():
            raise CastError('media_worker_failed','Local '+kind+' execution failed; inspect '+str(log))
        else:
            result=read_json(response)
            result['job_id']=ident
        record.update(status='succeeded' if result['status']=='ready' else result['status'],result=result,completed_at=time.time())
        if result.get('output'):
            record['artifacts'].append(result['output'])
        if result.get('qa'):
            record['artifacts'].append(str(Path(result['qa'])/'render.json'))
        if result.get('package'):
            record['artifacts'].append(result['package'])
        if result.get('index'):
            record['artifacts'].append(result['index'])
        write_json(directory/'job.json',record)
        return result
    except BaseException as exc:
        record.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',error=str(exc))
        write_json(directory/'job.json',record)
        raise


def author(root,operation,**kwargs):
    request=dict(operation=operation,**{k:str(Path(v).expanduser().resolve()) if k in ('output','package','script_file','text_file','profile_file','report_file','source_file') and v is not None else v for k,v in kwargs.items()})
    request['data_root'] = str(Path(root).resolve())
    if request.get('package') and not Path(request['package']).is_dir():
        raise CastError('missing_package','Provide a readable local production/authoring directory.')
    if request.get('output') and Path(request['output']).exists():
        raise CastError('output_exists','Use a new output directory; existing work is preserved.')
    return call(root,'authoring','authoring_worker.py',[],'authoring',request)


def render(root,package,output,check_only=False,scene_preview=False):
    project=Path(package).expanduser().resolve();target=Path(output).expanduser().resolve()
    if not (project/'package.json').is_file():
        raise CastError('missing_package','Provide an indexed local production package.')
    if target.exists() or target.with_name(target.stem+'-qa').exists():
        raise CastError('output_exists','Use a new output name; existing video and QA results are preserved.')
    args=['--package',project,'--output',target,'--browser-cache',root/'browsers/video']
    if check_only:
        args.append('--check-only')
    if scene_preview:
        args.append('--scene-preview')
    return call(root,'video','video_worker.py',args,'video')
