"""Feature registry and private environments; prepare only the requested feature."""
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile

from .common import CastError, digest, lock, read_json, result, write_json

RUNTIME = Path(__file__).resolve().parents[1]


def requirements_hash():
    return digest(RUNTIME / 'requirements-voice.txt') + ':' + digest(RUNTIME / 'constraints-voice-windows.txt')


def python_path(root):
    return root / 'envs/voice' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def environment(root):
    env = os.environ.copy()
    temporary = root / 'cache/tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    env.update(PYTHONUTF8='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               TEMP=str(temporary), TMP=str(temporary), UV_PYTHON_INSTALL_DIR=str(root/'python'),
               NLTK_DATA=str(root / 'cache/nltk'), HF_HOME=str(root / 'cache/huggingface'),
               PIP_CACHE_DIR=str(root / 'cache/pip'), UV_CACHE_DIR=str(root / 'cache/uv'))
    return env


def run_logged(args, root, name='setup', env=None):
    logs = root / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / (name + '.log')
    print('Running ' + str(args[0]) + '; log: ' + str(path), file=sys.stderr, flush=True)
    with path.open('ab') as f:
        p = subprocess.run([str(x) for x in args], stdout=f, stderr=f, env=env)
    if p.returncode:
        raise CastError('process_failed', f'Command failed ({p.returncode}). See {path}', 'inspect_log')


def download(url, dest, sha=None, size=None):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and (size is None or dest.stat().st_size == size) and (not sha or digest(dest) == sha):
        return
    part = dest.with_name(dest.name + '.part')
    offset = part.stat().st_size if part.exists() else 0
    if size is not None and offset > size:
        part.unlink()
        offset = 0
    if not (offset and size == offset):
        request = urllib.request.Request(url, headers={'User-Agent': 'codoop-cast/0.1', **({'Range': f'bytes={offset}-'} if offset else {})})
        with urllib.request.urlopen(request, timeout=90) as response:
            resumed = offset and response.status == 206
            if resumed and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                raise CastError('download_range', 'Unexpected download range.')
            with part.open('ab' if resumed else 'wb') as f:
                shutil.copyfileobj(response, f, 1024 * 1024)
    if size is not None and part.stat().st_size != size:
        raise CastError('download_incomplete', f'Incomplete download: {dest.name}', 'retry_setup')
    if sha and digest(part) != sha:
        part.unlink()
        raise CastError('checksum_failed', f'Checksum mismatch: {dest.name}', 'retry_setup')
    os.replace(part, dest)


def extract(archive, target):
    target = Path(target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if not (target / info.filename).resolve().is_relative_to(target):
                raise CastError('unsafe_archive', 'Archive path escapes destination.')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise CastError('unsafe_archive', 'Archive contains a symbolic link.')
        z.extractall(target)


def hardware():
    gpu = None
    try:
        p = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], capture_output=True, text=True, timeout=15)
        if p.returncode == 0:
            gpu = p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return dict(os=platform.system(), architecture=platform.machine(), nvidia=gpu)


def voice_check(root):
    state = root / 'features/voice.json'
    if not state.exists():
        return result('needs_setup', feature='voice', next_action='setup --feature voice')
    saved = read_json(state)
    if saved.get('requirements_hash') != requirements_hash() or saved.get('resources_hash') != digest(RUNTIME / 'resources-voice.json'):
        return result('needs_setup', feature='voice', next_action='setup --feature voice', reason='Plugin dependency or resource version changed.')
    missing = [str(root / p) for p in saved['required'] if not (root / p).is_file()]
    if missing or not python_path(root).exists():
        return result('needs_setup', feature='voice', missing=missing, next_action='setup --feature voice')
    return result(feature='voice', **{'model': saved['model'], 'verification': 'model_load', 'reference_inference_verified': saved.get('reference_inference_verified', False)})


def voice_setup(root):
    if voice_check(root)['status'] == 'ready':
        return voice_check(root)
    hw = hardware()
    if hw['os'] != 'Windows' or not hw['nvidia']:
        raise CastError('unsupported_backend', 'Initial release requires Windows with an NVIDIA GPU. AMD and Mac remain unverified.')
    manifest = read_json(RUNTIME / 'resources-voice.json')
    required_bytes = manifest['download_bytes'] + 8 * 1024**3
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < required_bytes:
        raise CastError('disk_space', 'Not enough free space for voice environment and model downloads.')
    cache = root / 'cache/downloads'
    source_zip = cache / 'gpt-sovits.zip'
    download(manifest['source']['url'], source_zip, manifest['source']['sha256'])
    source = root / 'engines/gpt-sovits'
    if not (source / 'GPT_SoVITS/TTS_infer_pack/TTS.py').exists():
        staging = root / 'engines/extracted'
        extract(source_zip, staging)
        folder = staging / ('GPT-SoVITS-' + manifest['source']['commit'])
        if source.exists():
            raise CastError('source_conflict', 'Incomplete engine source directory; inspect before repair.')
        folder.rename(source)
    # A private uv prepares Python; neither PATH nor global interpreters change.
    uv = root / 'tools/uv.exe'
    if not uv.exists():
        archive = cache / 'uv.zip'
        download(manifest['uv']['url'], archive, manifest['uv']['sha256'])
        extract(archive, root / 'tools')
    env = environment(root)
    env['UV_PYTHON_INSTALL_DIR'] = str(root / 'python')
    env['TEMP'] = str(root / 'cache/tmp')
    Path(env['TEMP']).mkdir(parents=True, exist_ok=True)
    py = python_path(root)
    if not py.exists():
        run_logged([uv, 'venv', '--python', '3.10', root / 'envs/voice'], root, env=env)
    req_hash = requirements_hash()
    deps_marker = root / 'envs/voice/codoop-deps.json'
    if not deps_marker.exists() or read_json(deps_marker).get('hash') != req_hash:
        run_logged([uv, 'pip', 'install', '--python', py, 'torch==2.5.1', 'torchaudio==2.5.1', '--index-url', 'https://download.pytorch.org/whl/cu124'], root, env=env)
        run_logged([uv, 'pip', 'install', '--python', py, '-r', RUNTIME / 'requirements-voice.txt', '-c', RUNTIME / 'constraints-voice-windows.txt'], root, env=env)
        write_json(deps_marker, {'hash': req_hash})
    required = []
    for asset in manifest['assets']:
        target = root / asset['target']
        print('Resource: ' + asset['target'], file=sys.stderr, flush=True)
        download(asset['url'], target, asset['sha256'], asset['size'])
        required.append(asset['target'])
    g2pw_zip = root / 'cache/downloads/G2PWModel.zip'
    extract(g2pw_zip, source / 'GPT_SoVITS/text')
    # Install known, pinned data archives; no dynamic NLTK index fetch or
    # relaxation of NLTK's network security settings is required.
    for asset in manifest['nltk_assets']:
        target = root / asset['target']
        download(asset['url'], target, asset['sha256'], asset['size'])
        extract(target, target.parent)
        required.append(asset['target'])
    required += ['engines/gpt-sovits/GPT_SoVITS/TTS_infer_pack/TTS.py', 'engines/gpt-sovits/GPT_SoVITS/text/G2PWModel/g2pW.onnx']
    with lock(root, 'gpu-voice'):
        run_logged([py, RUNTIME / 'worker.py', '--root', root, '--probe'], root, 'probe', env)
    write_json(root / 'features/voice.json', {'required': required, 'model': manifest['source']['commit'] + ':v2Pro',
                                           'reference_inference_verified': False,
                                           'requirements_hash': requirements_hash(), 'resources_hash': digest(RUNTIME / 'resources-voice.json')})
    config = read_json(root / 'config.json') if (root / 'config.json').exists() else {'schema_version': 1, 'features': {}}
    config.setdefault('features', {}).setdefault('voice', {}).update({'backend': 'cuda', 'model': 'v2Pro'})
    write_json(root / 'config.json', config)
    return voice_check(root)


def alignment_requirements_hash():
    return digest(RUNTIME / 'requirements-alignment.txt') + ':' + digest(RUNTIME / 'constraints-alignment-windows.txt')


def alignment_python(root):
    return root / 'envs/alignment' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def alignment_check(root):
    state = root / 'features/alignment.json'
    if not state.exists():
        return result('needs_setup',feature='alignment',next_action='setup --feature alignment')
    saved = read_json(state)
    valid = saved.get('requirements_hash') == alignment_requirements_hash() and saved.get('resources_hash') == digest(RUNTIME / 'resources-alignment.json')
    missing = [p for p in saved.get('required',[]) if not (root / p).is_file()]
    if not valid or missing or not alignment_python(root).is_file():
        return result('needs_setup',feature='alignment',missing=missing,next_action='setup --feature alignment')
    return result(feature='alignment',model=saved['model'],verification='model_load')


def alignment_setup(root):
    if alignment_check(root)['status'] == 'ready':
        return alignment_check(root)
    hw = hardware()
    if hw['os'] != 'Windows' or not hw['nvidia']:
        raise CastError('unsupported_backend','Initial alignment backend requires Windows with NVIDIA; other backends remain unverified.')
    root.mkdir(parents=True,exist_ok=True)
    manifest = read_json(RUNTIME / 'resources-alignment.json')
    if shutil.disk_usage(root).free < sum(a['size'] for a in manifest['assets']) + 6*1024**3:
        raise CastError('disk_space','Not enough free space for alignment environment and model.')
    uv = root / 'tools/uv.exe'
    if not uv.exists():
        spec = read_json(RUNTIME / 'resources-voice.json')['uv']
        archive = root / 'cache/downloads/uv.zip'
        download(spec['url'],archive,spec['sha256'])
        extract(archive,root / 'tools')
    env = environment(root)
    env.update(UV_PYTHON_INSTALL_DIR=str(root / 'python'),TEMP=str(root / 'cache/tmp'))
    Path(env['TEMP']).mkdir(parents=True,exist_ok=True)
    py = alignment_python(root)
    if not py.exists():
        run_logged([uv,'venv','--python','3.10',root / 'envs/alignment'],root,'alignment-setup',env)
    marker = root / 'envs/alignment/codoop-deps.json'
    if not marker.exists() or read_json(marker).get('hash') != alignment_requirements_hash():
        run_logged([uv,'pip','install','--python',py,'torch==2.5.1','torchaudio==2.5.1','--index-url','https://download.pytorch.org/whl/cu124'],root,'alignment-setup',env)
        run_logged([uv,'pip','install','--python',py,'-r',RUNTIME / 'requirements-alignment.txt','-c',RUNTIME / 'constraints-alignment-windows.txt'],root,'alignment-setup',env)
        write_json(marker,{'hash':alignment_requirements_hash()})
    for asset in manifest['assets']:
        print('Alignment resource: '+asset['target'],file=sys.stderr,flush=True)
        download(asset['url'],root / asset['target'],asset['sha256'],asset['size'])
    model_dir = root / 'models/qwen3-forced-aligner-0.6b-hf'
    with lock(root,'gpu-voice'):
        run_logged([py,RUNTIME / 'alignment_worker.py','--probe','--model',model_dir],root,'alignment-probe',env)
    write_json(root / 'features/alignment.json',dict(model=manifest['revision'],requirements_hash=alignment_requirements_hash(),
        resources_hash=digest(RUNTIME / 'resources-alignment.json'),required=[a['target'] for a in manifest['assets']]))
    config = read_json(root / 'config.json') if (root / 'config.json').exists() else {'schema_version':1,'features':{}}
    config.setdefault('features',{}).setdefault('alignment',{}).update(backend='cuda',model=manifest['revision'])
    write_json(root / 'config.json',config)
    return alignment_check(root)


def feature_python(root,name):
    return root / ('envs/'+name) / ('Scripts/python.exe' if os.name=='nt' else 'bin/python')


def tool_requirements_hash(name):
    return digest(RUNTIME / ('requirements-'+name+'.txt'))+':'+digest(RUNTIME / ('constraints-'+name+'-windows.txt'))


def tool_check(root,name):
    state=root/'features'/(name+'.json')
    if not state.exists():
        return result('needs_setup',feature=name,next_action='setup --feature '+name)
    saved=read_json(state)
    valid=saved.get('requirements_hash')==tool_requirements_hash(name)
    if name=='video':
        valid=valid and saved.get('resources_hash')==digest(RUNTIME/'resources-video.json')
    if not valid or not feature_python(root,name).is_file() or any(not (root/p).is_file() for p in saved.get('required',[])):
        return result('needs_setup',feature=name,next_action='setup --feature '+name)
    return result(feature=name,verification=saved['verification'])


def tool_setup(root,name):
    if tool_check(root,name)['status']=='ready':
        return tool_check(root,name)
    if platform.system()!='Windows':
        raise CastError('unsupported_backend','Private authoring/video setup is currently validated on Windows only.')
    root.mkdir(parents=True,exist_ok=True)
    uv=root/'tools/uv.exe'
    if not uv.exists():
        spec=read_json(RUNTIME/'resources-voice.json')['uv']
        archive=root/'cache/downloads/uv.zip'
        download(spec['url'],archive,spec['sha256'])
        extract(archive,root/'tools')
    env=environment(root)
    env.update(UV_PYTHON_INSTALL_DIR=str(root/'python'),PLAYWRIGHT_BROWSERS_PATH=str(root/'browsers/video'))
    py=feature_python(root,name)
    if not py.exists():
        run_logged([uv,'venv','--python','3.10',root/('envs/'+name)],root,name+'-setup',env)
    marker=root/('envs/'+name+'/codoop-deps.json')
    if not marker.exists() or read_json(marker).get('hash')!=tool_requirements_hash(name):
        run_logged([uv,'pip','install','--python',py,'-r',RUNTIME/('requirements-'+name+'.txt'),'-c',RUNTIME/('constraints-'+name+'-windows.txt')],root,name+'-setup',env)
        write_json(marker,{'hash':tool_requirements_hash(name)})
    required=[]
    state=dict(requirements_hash=tool_requirements_hash(name),verification='schema_validation')
    if name=='video':
        spec=read_json(RUNTIME/'resources-video.json')
        if not (root/spec['browser_relative_path']).exists():
            run_logged([py,'-m','playwright','install','chromium','--only-shell'],root,'video-browser',env)
        if digest(root/spec['browser_relative_path'])!=spec['browser_sha256']:
            raise CastError('browser_mismatch','Private browser executable differs from the pinned build. Inspect the video cache before repair.')
        run_logged([py,RUNTIME/'video_worker.py','--probe','--root',root],root,'video-probe',env)
        browser_dir=root/'browsers/video/chromium_headless_shell-1194'
        required=[str(p.relative_to(root)) for p in browser_dir.rglob('*') if p.is_file()]
        state.update(resources_hash=digest(RUNTIME/'resources-video.json'),verification='browser_launch_and_screenshot')
    else:
        run_logged([py,'-c','from jsonschema import Draft202012Validator; Draft202012Validator.check_schema({"type":"object"})'],root,'authoring-probe',env)
    state['required']=required
    write_json(root/'features'/(name+'.json'),state)
    config=read_json(root/'config.json') if (root/'config.json').exists() else {'schema_version':1,'features':{}}
    config.setdefault('features',{}).setdefault(name,{}).update(environment=name)
    write_json(root/'config.json',config)
    return tool_check(root,name)


FEATURES = {'voice': {'check': voice_check, 'setup': voice_setup},'alignment':{'check':alignment_check,'setup':alignment_setup},
    'authoring':{'check':lambda root:tool_check(root,'authoring'),'setup':lambda root:tool_setup(root,'authoring')},
    'video':{'check':lambda root:tool_check(root,'video'),'setup':lambda root:tool_setup(root,'video')}}


def doctor(root, feature=None):
    from .data_layout import inspect
    names = [feature] if feature else list(FEATURES)
    for name in names:
        if name not in FEATURES:
            raise CastError('unknown_feature', f'Feature not implemented: {name}')
    states = {name: FEATURES[name]['check'](root) for name in names}
    return result('ready' if all(x['status'] == 'ready' for x in states.values()) else 'needs_setup', root=str(root), data_layout=inspect(root), hardware=hardware(), features=states)


def setup(root, feature):
    if feature not in FEATURES:
        raise CastError('unknown_feature', f'Feature not implemented: {feature}')
    from .data_layout import initialize
    initialize(root)
    with lock(root, 'setup'):
        return FEATURES[feature]['setup'](root)
