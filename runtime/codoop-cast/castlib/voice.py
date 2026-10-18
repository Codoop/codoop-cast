import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import wave

from .common import CastError, digest, item_path, lock, new_id, read_json, result, write_json
from .setup import RUNTIME, environment, python_path, setup, voice_check


def ensure(root):
    if voice_check(root)['status'] != 'ready':
        setup(root, 'voice')


def worker(root, *args, log='worker'):
    ensure(root)
    path = root / 'logs' / (log + '.log')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('ab') as f:
        p = subprocess.run([str(python_path(root)), str(RUNTIME / 'worker.py'), '--root', str(root), *map(str, args)], env=environment(root), stdout=f, stderr=f)
    if p.returncode:
        raise CastError('engine_failed', f'Engine failed. Inspect {path}', 'inspect_log')


def list_voices(root):
    return [read_json(p) for p in sorted((root / 'voices').glob('*/voice.json'))]


def select_voice(root, query=None):
    voices = list_voices(root)
    matches = [v for v in voices if query in (v['id'], v['name'])] if query else voices
    if len(matches) != 1:
        raise CastError('voice_selection', 'Specify a voice name or ID; no unique voice was selected.', 'voice list')
    return matches[0]


def create_voice(root, audio, reference_text=None, name=None, language='zh'):
    audio = Path(audio).expanduser().resolve()
    if not audio.is_file():
        raise CastError('invalid_reference', 'Provide a readable local audio file.')
    ensure(root)
    if shutil.disk_usage(root).free < audio.stat().st_size:
        raise CastError('disk_space', 'Not enough space in the data directory to preserve the original audio.')
    ident = new_id()
    directory = root / 'voices' / ident
    directory.mkdir(parents=True)
    original = directory / ('original' + audio.suffix.lower())
    shutil.copyfile(audio, original)
    print('Preparing reference audio; log: ' + str(root / 'logs' / ('reference-' + ident + '.log')), file=sys.stderr, flush=True)
    # Preserve failed imports for diagnostics, but never list them as usable voices.
    args = ['--prepare', original, '--output', directory / 'reference.wav', '--language', language]
    if reference_text and reference_text.strip():
        args += ['--reference-text', reference_text.strip()]
    try:
        worker(root, *args, log='reference-' + ident)
    except CastError:
        error = directory / 'reference.error.json'
        if error.exists():
            detail = read_json(error)
            raise CastError(detail['code'], detail['message'])
        raise
    prepared = read_json(directory / 'reference.json')
    voice = dict(schema_version=1, id=ident, name=name or audio.stem,
                 reference=str(directory / 'reference.wav'), original=str(original),
                 reference_text=prepared['text'], language=language, selection=prepared,
                 reference_sha256=digest(directory / 'reference.wav'), created_at=time.time())
    if prepared['needs_confirmation']:
        write_json(directory / 'draft.json', voice)
        return result('needs_input', voice=voice, next_action='Confirm the selected excerpt and its transcript; use voice confirm with the corrected reference text.')
    write_json(directory / 'voice.json', voice)
    return result(voice=voice)


def confirm_voice(root, ident, reference_text):
    directory = item_path(root, 'voices', ident)
    if (directory / 'voice.json').exists():
        raise CastError('already_confirmed', 'This voice is already saved. Import a new version to change it.')
    voice = read_json(directory / 'draft.json')
    if not reference_text.strip():
        raise CastError('empty_transcript', 'Confirm the selected clip transcript.')
    if digest(voice['reference']) != voice['reference_sha256']:
        raise CastError('reference_changed', 'Selected reference file changed. Import the source again.')
    voice['reference_text'] = reference_text.strip()
    voice['selection'].update(needs_confirmation=False, confirmed_by_user=True)
    write_json(directory / 'voice.json', voice)
    return result(voice=voice)


def split_text(text, limit=180):
    text = text.strip()
    if not text or not any(c.isalnum() for c in text):
        raise CastError('empty_text', 'Provide a nonempty narration script.')
    sentences = re.findall(r'[^。！？!?\n]+[。！？!?\n]*|[。！？!?]+', text)
    groups, current = [], ''
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        while len(sentence) > limit:
            if current:
                groups.append(current)
                current = ''
            # Prefer punctuation/space over breaking a long token.
            boundary = max(sentence.rfind(ch, 0, limit + 1) for ch in ('，', ',', '；', ';', ' '))
            boundary = boundary + 1 if boundary > limit // 2 else limit
            groups.append(sentence[:boundary])
            sentence = sentence[boundary:]
        if len(current) + len(sentence) > limit and current:
            groups.append(current)
            current = ''
        current += sentence
    if current:
        groups.append(current)
    return groups


def narration_text(text):
    """Conservative pause hints; preserve every non-punctuation character."""
    parts = re.split(r'([。！？!?\n])', text.strip())
    for index in range(0, len(parts), 2):
        sentence = parts[index]
        sentence = sentence.replace('；', '。')
        if len(sentence) >= 28:
            start = 0
            chars = list(sentence)
            for pos, char in enumerate(chars):
                if char == '，' and pos - start >= 14 and len(chars) - pos - 1 >= 8:
                    chars[pos] = '。'
                    start = pos + 1
            sentence = ''.join(chars)
        parts[index] = sentence
    return ''.join(parts)


def load_job(root, ident):
    return read_json(item_path(root, 'jobs', ident) / 'job.json')


def save_job(root, job):
    write_json(item_path(root, 'jobs', job['id']) / 'job.json', job)


def wav_info(path):
    with wave.open(str(path), 'rb') as f:
        if f.getnchannels() != 1 or f.getsampwidth() != 2 or not f.getnframes():
            raise CastError('invalid_audio', 'Expected nonempty mono PCM16 audio.')
        return dict(samples=f.getnframes(), sample_rate=f.getframerate())


def export_job(root, job, output=None):
    from .script_audio import verify_script_job
    script = verify_script_job(job)
    if output and script:
        dest = Path(output).expanduser().resolve()
        for path in (dest, dest.with_suffix('.json'), dest.parent/'script.json', dest.parent/'original.txt', dest.parent/'narration.txt'):
            if path.exists():
                raise CastError('output_exists', 'Use a new voice version directory; output exists: '+str(path))
    if any(not s.get('selected') for s in job['segments']):
        raise CastError('incomplete_job', 'Some segments are missing; resume the job first.')
    directory = item_path(root, 'jobs', job['id'])
    target = directory / ('narration-' + new_id() + '.wav')
    temp = target.with_suffix('.tmp')
    boundaries, rate, offset = [], None, 0
    try:
        with wave.open(str(temp), 'wb') as out:
            for index, segment in enumerate(job['segments']):
                path = directory / segment['selected']
                info = wav_info(path)
                if rate is None:
                    rate = info['sample_rate']
                    out.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
                if rate != info['sample_rate']:
                    raise CastError('sample_rate_mismatch', 'Segment rates differ; refusing an inaccurate timeline.')
                if index:
                    pause = round(rate * job.get('synthesis', {}).get('join_interval', .2))
                    out.writeframes(b'\x00\x00' * pause)
                    offset += pause
                start = offset
                with wave.open(str(path), 'rb') as audio:
                    while block := audio.readframes(65536):
                        out.writeframes(block)
                offset += info['samples']
                selected = next((a for a in segment['attempts'] if a.get('file') == segment['selected']),{}) if 'attempts' in segment else {}
                boundaries.append(dict(segment_id=segment['id'], start_sample=start, end_sample=offset, file=str(path), text=segment['text'],
                    normalized_text=selected.get('normalized_text'),normalization_source=selected.get('normalization_source'),
                    text_mapping=selected.get('text_mapping'),mapping_error=selected.get('mapping_error')))
                if script:
                    boundaries[-1].update({key:segment[key] for key in ('script_spans','display_span','display_text','spoken_text','requested_mapping')})
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    manifest = target.with_suffix('.json')
    write_json(manifest, dict(schema_version=1, job_id=job['id'], language=job.get('language', 'zh'), voice=job['voice'], model=job.get('model'),
               synthesis=job.get('synthesis'), original_text=job.get('original_text'),
               narration_text=job.get('narration_text'), script_fingerprint=job.get('script_fingerprint'),
               sample_rate=rate, total_samples=offset, segments=boundaries, audio=str(target)))
    job['artifacts'] = [str(target), str(manifest)]
    job['artifacts'] += [str(directory / name) for name in ('original.txt', 'narration.txt') if (directory / name).exists()]
    save_job(root, job)
    if output:
        dest = Path(output).expanduser().resolve()
        if dest.exists():
            raise CastError('output_exists', f'Output already exists: {dest}. Generated audio remains at {target}.')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, dest)
        job['artifacts'].append(str(dest))
        if script:
            copied = read_json(manifest); copied['audio'] = str(dest)
            write_json(dest.with_suffix('.json'), copied)
            write_json(dest.parent/'script.json', script)
            for name in ('original.txt','narration.txt'):
                shutil.copyfile(directory/name,dest.parent/name)
            job['artifacts'] += [str(dest.with_suffix('.json')),str(dest.parent/'script.json'),str(dest.parent/'original.txt'),str(dest.parent/'narration.txt')]
        save_job(root, job)
    return result(job_id=job['id'], artifacts=job['artifacts'])


def generate(root, text=None, voice_query=None, speed=1.0, output=None, script_file=None, language=None):
    if not math.isfinite(speed) or not .5 <= speed <= 2:
        raise CastError('invalid_speed', 'Speed must be between 0.5 and 2.')
    from .script_audio import prepare_script,fingerprint
    script = read_json(script_file) if script_file else None
    if script:
        chunks = prepare_script(script)
        text = '\n\n'.join(p['display_text'] for p in script['data']['paragraphs'])
        texts = [narration_text(chunk['spoken_text']) for chunk in chunks]
        spoken = '\n\n'.join(texts)
    else:
        spoken = narration_text(text)
        texts = split_text(spoken, limit=100)
    from .config import resolve, speech_language
    selected_language = script['data']['language'] if script else resolve(Path.cwd(), language, root)['output_language']
    backend_language = speech_language(selected_language)
    if script and language and speech_language(language) != backend_language:
        raise CastError('language_mismatch', 'The task language differs from the pinned script; create a translated script revision first.')
    voice = select_voice(root, voice_query)
    ensure(root)
    ident = new_id()
    job = dict(schema_version=1, id=ident, language=selected_language, text_language=backend_language, voice=voice, speed=speed, status='pending', created_at=time.time(),
               model=read_json(root / 'features/voice.json')['model'], original_text=text, narration_text=spoken,
               synthesis=dict(policy='natural-pauses-v1', fragment_interval=.15, join_interval=0.),
               segments=[dict(id=new_id(), text=t, status='pending', attempts=[], selected=None) for t in texts])
    if script:
        job.update(script_artifact=script,script_fingerprint=fingerprint(script))
        for segment,chunk in zip(job['segments'],chunks):
            segment.update(chunk)
    save_job(root, job)
    directory = item_path(root, 'jobs', ident)
    (directory / 'original.txt').write_text(text, encoding='utf-8')
    (directory / 'narration.txt').write_text(spoken, encoding='utf-8')
    return run_job(root, ident, output=output)


def run_job(root, ident, retry=None, replacement=None, output=None):
    ensure(root)
    with lock(root, 'gpu-voice'):
        job = load_job(root, ident)
        from .script_audio import verify_script_job
        verify_script_job(job)
        if job.get('script_artifact') and replacement is not None:
            raise CastError('pinned_script', 'Change the script revision and create a new task; structured retries preserve pinned text.')
        directory = item_path(root, 'jobs', ident)
        for segment in job['segments']:
            for attempt in segment['attempts']:
                if attempt['status'] == 'running':
                    attempt.update(status='interrupted', error='Previous worker ended before completing this attempt.')
            if segment['status'] == 'running':
                segment['status'] = 'interrupted'
        if retry is not None:
            if retry < 1 or retry > len(job['segments']):
                raise CastError('invalid_segment', 'Segment index is one-based and out of range.')
            segment = job['segments'][retry - 1]
            if replacement is not None:
                if not replacement.strip():
                    raise CastError('empty_text', 'Replacement text must not be empty.')
                segment['text'] = narration_text(replacement) if job.get('synthesis') else replacement.strip()
                if job.get('synthesis'):
                    job['narration_text'] = ''.join(s['text'] for s in job['segments'])
                    (directory / 'narration.txt').write_text(job['narration_text'], encoding='utf-8')
            segment['selected'] = None
            segment['status'] = 'pending'
            job['artifacts'] = []
        (directory / 'cancel').unlink(missing_ok=True)
        job.update(status='running', error=None)
        save_job(root, job)
        try:
            worker(root, '--job', ident, log='job-' + ident)
            job = load_job(root, ident)
            if job['status'] != 'succeeded':
                return result(job['status'], job_id=ident, error={'code': 'generation_incomplete', 'message': job.get('error') or job['status']}, next_action='speech resume --job ' + ident)
            return export_job(root, job, output)
        except BaseException as exc:
            job = load_job(root, ident)
            job.update(status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed', error=str(exc))
            save_job(root, job)
            raise
