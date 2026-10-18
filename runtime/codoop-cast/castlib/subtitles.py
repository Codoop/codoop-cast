"""Independent local subtitle tasks; no voice environment needed for external input."""
from pathlib import Path
import shutil
import subprocess
import time
import wave

from .common import CastError,digest,item_path,lock,new_id,read_json,result,write_json
from .setup import RUNTIME,alignment_check,alignment_python,environment,setup
from .voice import load_job,wav_info
from .textmap import normalization_map


def verify_audio_segments(manifest):
    """The selected chunks must actually occupy these samples in the export."""
    with wave.open(str(manifest['audio']),'rb') as final:
        if final.getnchannels()!=1 or final.getsampwidth()!=2 or final.getframerate()!=manifest['sample_rate'] or final.getnframes()!=manifest['total_samples']:
            raise CastError('audio_manifest_mismatch','Exported audio no longer matches its sample manifest.')
        previous=0
        for boundary in manifest['segments']:
            if not previous <= boundary['start_sample'] < boundary['end_sample'] <= final.getnframes():
                raise CastError('audio_manifest_mismatch','Audio segment ranges are invalid.')
            with wave.open(str(boundary['file']),'rb') as chunk:
                if chunk.getnchannels()!=1 or chunk.getsampwidth()!=2 or chunk.getframerate()!=final.getframerate() or chunk.getnframes()!=boundary['end_sample']-boundary['start_sample']:
                    raise CastError('audio_manifest_mismatch','Selected audio chunk changed after export.')
                final.setpos(boundary['start_sample'])
                while block:=chunk.readframes(65536):
                    if block!=final.readframes(len(block)//2):
                        raise CastError('audio_manifest_mismatch','Selected chunk content differs from the exported audio.')
            previous=boundary['end_sample']


def generate(root,source_job=None,audio=None,text_file=None,spoken_file=None,output=None,language=None):
    destination=Path(output).expanduser().resolve() if output else None
    if destination and destination.exists():
        raise CastError('output_exists','Use a new subtitle output directory; existing files are preserved.')
    if bool(source_job) == bool(audio):
        raise CastError('invalid_subtitle_input','Provide either a speech job or local audio with its script.')
    if source_job and (text_file or spoken_file):
        raise CastError('invalid_subtitle_input','A speech job supplies its own selected texts; do not replace them with unrelated files.')
    if source_job:
        selected_job=load_job(root,source_job)
        if selected_job.get('kind') == 'subtitles' or selected_job.get('status') != 'succeeded' or not selected_job.get('artifacts'):
            raise CastError('speech_not_ready','Select a completed speech task with its current exported audio.')
    if audio:
        audio=Path(audio).expanduser().resolve()
        if not audio.is_file() or not text_file:
            raise CastError('missing_subtitle_input','External audio requires a readable local audio file and its UTF-8 transcript.')
        text=Path(text_file).read_text(encoding='utf-8-sig').strip()
        spoken=Path(spoken_file).read_text(encoding='utf-8-sig').strip() if spoken_file else text
        mapping=normalization_map(text,spoken)
    from .config import speech_language
    from .config import resolve
    if source_job and language and speech_language(language) != speech_language(selected_job.get('language', 'zh')):
        raise CastError('language_mismatch', 'Subtitle language must match the pinned audio; translate and synthesize a new revision first.')
    language = selected_job.get('language', 'zh') if source_job else resolve(Path(text_file).parent, language, root)['output_language']
    speech_language(language)
    if alignment_check(root)['status'] != 'ready':
        setup(root,'alignment')
    ident=new_id()
    directory=item_path(root,'jobs',ident)
    source=directory/'input'
    source.mkdir(parents=True)
    record=dict(schema_version=1,id=ident,kind='subtitles',status='running',created_at=time.time(),
                source_job=source_job,artifacts=[],review_required=True)
    write_json(directory/'job.json',record)
    log=root/'logs'/('subtitles-'+ident+'.log')
    log.parent.mkdir(parents=True,exist_ok=True)
    py=alignment_python(root)
    model=root/'models/qwen3-forced-aligner-0.6b-hf'
    try:
        with lock(root,'gpu-voice'):
            if source_job:
                job=load_job(root,source_job)
                if job.get('kind') == 'subtitles' or job.get('status') != 'succeeded' or not job.get('artifacts'):
                    raise CastError('speech_not_ready','Select a completed speech task with its current exported audio.')
                job=read_json(item_path(root,'jobs',source_job)/'job.json')
                manifest=read_json(job['artifacts'][1])
                from .script_audio import verify_script_job
                script=verify_script_job(job)
                if script and manifest.get('script_fingerprint')!=job['script_fingerprint']:
                    raise CastError('stale_audio_manifest','Export no longer refers to the pinned script.')
                source_dir=item_path(root,'jobs',source_job)
                if len(manifest['segments']) != len(job['segments']):
                    raise CastError('stale_audio_manifest','Export the current speech task before creating subtitles.')
                for segment,boundary in zip(job['segments'],manifest['segments']):
                    path=(source_dir/segment['selected']).resolve()
                    if Path(boundary['file']).resolve() != path or boundary['text'] != segment['text']:
                        raise CastError('stale_audio_manifest','Speech selection changed after export.')
                    if script and any(boundary.get(key)!=segment.get(key) for key in ('script_spans','display_span','display_text','spoken_text','requested_mapping')):
                        raise CastError('stale_audio_manifest','Exported script ranges differ from the pinned chunks.')
                    if not boundary.get('normalized_text') and any(c.isascii() and c.isalnum() for c in segment['text']):
                        raise CastError('legacy_normalization_missing','This legacy mixed-text narration has no recorded TTS normalization. Generate a new narration to capture its actual spoken form.')
                    if boundary.get('mapping_error'):
                        raise CastError('unmapped_normalization',boundary['mapping_error']['message'])
                    segment['selected']=str(path)
                record['source_audio_sha256']=digest(job['artifacts'][0])
            else:
                with log.open('ab') as stream:
                    p=subprocess.run([str(py),str(RUNTIME/'alignment_worker.py'),'--prepare',str(audio),'--output',str(source/'audio.wav')],
                        env=environment(root),stdout=stream,stderr=stream)
                if p.returncode:
                    error=read_json(source/'audio.error.json') if (source/'audio.error.json').exists() else {}
                    raise CastError(error.get('code','audio_decode_failed'),error.get('message','Audio decoding failed. Inspect '+str(log)))
                info=wav_info(source/'audio.wav')
                boundary=dict(segment_id='external',start_sample=0,end_sample=info['samples'],file=str(source/'audio.wav'),
                              text=text,normalized_text=spoken,text_mapping=mapping)
                manifest=dict(sample_rate=info['sample_rate'],total_samples=info['samples'],segments=[boundary],audio=str(source/'audio.wav'))
                job=dict(language=language, original_text=text,segments=[dict(id='external',text=text,selected=str(source/'audio.wav'))],artifacts=[])
                record['source_audio_sha256']=digest(audio)
            verify_audio_segments(manifest)
            write_json(source/'manifest.json',manifest)
            job['artifacts']=[manifest['audio'],str(source/'manifest.json')]
            write_json(source/'job.json',job)
            write_json(directory/'job.json',record)
            with log.open('ab') as stream:
                p=subprocess.run([str(py),str(RUNTIME/'alignment_worker.py'),'--job-dir',str(source),'--model',str(model),
                    '--output',str(directory/'result'),'--artifact-prefix',ident],env=environment(root),stdout=stream,stderr=stream)
            if p.returncode:
                raise CastError('alignment_failed','Alignment could not finish. Inspect '+str(log))
        checks=read_json(directory/'result/checks.json')
        files=sorted(p for p in (directory/'result').rglob('*') if p.is_file())
        cancelled=checks.get('state') == 'cancelled'
        record.update(status='cancelled' if cancelled else ('succeeded' if checks['srt_exported'] else 'needs_input'),checks=checks,
                      artifacts=[str(p) for p in files],completed_at=time.time())
        write_json(directory/'job.json',record)
        if destination:
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(directory/'result',destination)
            record['artifacts'] += [str(destination/p.relative_to(directory/'result')) for p in files]
            write_json(directory/'job.json',record)
        return result('cancelled' if cancelled else ('ready' if checks['srt_exported'] else 'needs_input'),job_id=ident,artifacts=record['artifacts'],
            review_required=True,issues=checks['issues'],warnings=checks['warnings'],
            next_action='Preview subtitles against the selected audio; resolve reported timing issues before video export.')
    except BaseException as exc:
        record.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',error=str(exc))
        write_json(directory/'job.json',record)
        raise
