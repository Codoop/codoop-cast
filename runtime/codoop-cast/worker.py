"""Invoked only with the private voice interpreter. No web server."""
import argparse
import contextlib
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

from castlib.common import CastError, digest, item_path, new_id, read_json, write_json


@contextlib.contextmanager
def capture_normalized_text(engine):
    """Observe the same frontend call used by synthesis, without rerunning it."""
    frontend = engine.text_preprocessor
    original = frontend.preprocess
    captured = []
    def preprocess(*args, **kwargs):
        data = original(*args, **kwargs)
        captured.extend(item['norm_text'] for item in data)
        return data
    frontend.preprocess = preprocess
    try:
        yield captured
    finally:
        frontend.preprocess = original


def prepare(root, source, target, reference_text=None, language='zh'):
    import imageio_ffmpeg
    import numpy as np
    import soundfile as sf
    import subprocess
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.prepare.wav')
    try:
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-y', '-i', str(source), '-ac', '1', '-ar', '32000', '-c:a', 'pcm_s16le', str(temp)], check=True)
        info = sf.info(temp)
        rate = info.samplerate
        duration = info.frames / rate
        if duration < 3:
            raise CastError('reference_too_short', 'There is not enough source audio. Provide a longer recording; no manual cutting is needed.')
        peak = 0.0
        with sf.SoundFile(temp) as audio:
            for block in audio.blocks(blocksize=rate * 10):
                if not np.isfinite(block).all():
                    raise CastError('invalid_reference', 'Reference audio contains invalid samples.')
                peak = max(peak, float(np.max(np.abs(block))))
        if peak < .001:
            raise CastError('silent_reference', 'Reference audio is silent or invalid.')
        if duration <= 10 and reference_text:
            selection = dict(start_seconds=0, end_seconds=duration, text=reference_text.strip(),
                             selection='user_transcript', needs_confirmation=False, speaker_check='not_performed')
        else:
            from faster_whisper import WhisperModel
            from castlib.reference import choose_reference
            model_path = root / 'models/faster-whisper-small'
            # CPU int8 keeps transcription independent of CUDA/cuDNN and frees
            # GPU memory for TTS. No model is fetched during inference.
            model = WhisperModel(str(model_path), device='cpu', compute_type='int8', cpu_threads=6, local_files_only=True)
            recognized, asr_info = model.transcribe(str(temp), language=language, beam_size=5,
                                                   word_timestamps=True, vad_filter=True,
                                                   condition_on_previous_text=False)
            segments = []
            for segment in recognized:
                segments.append(dict(start=segment.start, end=segment.end, text=segment.text,
                                     avg_logprob=segment.avg_logprob, no_speech_prob=segment.no_speech_prob,
                                     words=[dict(start=w.start, end=w.end, word=w.word, probability=w.probability) for w in (segment.words or [])]))
                print(f'Transcribed {segment.end:.1f}/{duration:.1f} seconds', flush=True)
            write_json(target.with_name('transcription.json'), dict(language=asr_info.language, segments=segments))
            selection = choose_reference(segments, duration)
            if language == 'zh':
                from opencc import OpenCC
                selection['text'] = OpenCC('t2s').convert(selection['text'])
        with sf.SoundFile(temp) as audio:
            start = round(selection['start_seconds'] * rate)
            stop = min(info.frames, round(selection['end_seconds'] * rate))
            audio.seek(start)
            clip = audio.read(stop - start)
        if not 3 <= len(clip)/rate <= 10 or np.max(np.abs(clip)) < .001:
            raise CastError('invalid_selection', 'Selected reference is not usable; choose a different utterance.')
        sf.write(target, clip, rate, subtype='PCM_16')
        write_json(target.with_suffix('.json'), dict(source_duration_seconds=duration, sample_rate=rate,
                   start_sample=start, end_sample=stop, supplied_source_text=reference_text, **selection))
    finally:
        temp.unlink(missing_ok=True)


def load_engine(root, model='v2'):
    source = root / 'engines/gpt-sovits'
    os.chdir(source)
    sys.path[:0] = [str(source), str(source / 'GPT_SoVITS')]
    import imageio_ffmpeg
    tools = root / 'tools'
    tools.mkdir(parents=True, exist_ok=True)
    ffmpeg = tools / 'ffmpeg.exe'
    if not ffmpeg.exists():
        shutil.copyfile(imageio_ffmpeg.get_ffmpeg_exe(), ffmpeg)
    os.environ['PATH'] = str(tools) + os.pathsep + os.environ.get('PATH', '')
    os.environ['version'] = 'v2'
    # Upstream uses the jieba_fast API. Pure-Python jieba offers the needed
    # tokenizer/posseg interface without requiring a C compiler on Windows.
    import jieba
    import jieba.posseg
    sys.modules['jieba_fast'] = jieba
    sys.modules['jieba_fast.posseg'] = jieba.posseg
    import torch
    if not torch.cuda.is_available():
        raise CastError('cuda_unavailable', 'CUDA is unavailable in the private voice environment; inspect driver and PyTorch installation.')
    from TTS_infer_pack.TTS import TTS, TTS_Config
    variants = {
        'v2': ('gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt', 'gsv-v2final-pretrained/s2G2333k.pth'),
        'v2Pro': ('s1v3.ckpt', 'v2Pro/s2Gv2Pro.pth'),
        'v2ProPlus': ('s1v3.ckpt', 'v2Pro/s2Gv2ProPlus.pth'),
    }
    if model not in variants:
        raise CastError('unsupported_model', 'Unknown internal inference model.')
    semantic, acoustic = variants[model]
    base = 'GPT_SoVITS/pretrained_models/'
    if not (source / (base + semantic)).exists() or not (source / (base + acoustic)).exists():
        raise CastError('missing_model', 'Requested inference weights have not been prepared.')
    config = TTS_Config({'version': 'v2', 'custom': {
        'device': 'cuda', 'is_half': True,
        't2s_weights_path': base + semantic,
        'vits_weights_path': base + acoustic,
        'bert_base_path': 'GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large',
        'cnhuhbert_base_path': 'GPT_SoVITS/pretrained_models/chinese-hubert-base'}})
    engine = TTS(config)
    if model != 'v2' and (not engine.is_v2pro or engine.configs.version != model):
        raise CastError('model_mismatch', 'Upstream did not recognize the requested Pro weights.')
    return engine


def process(root, ident, engine):
    import numpy as np
    import soundfile as sf
    from castlib.voice import wav_info
    directory = item_path(root, 'jobs', ident)
    path = directory / 'job.json'
    job = read_json(path)
    voice = job['voice']
    if digest(voice['reference']) != voice['reference_sha256']:
        raise CastError('reference_changed', 'Saved reference audio changed; import it as a new voice.')
    for index, segment in enumerate(job['segments']):
        if (directory / 'cancel').exists():
            job['status'] = 'cancelled'
            write_json(path, job)
            return
        if segment.get('selected'):
            wav_info(directory / segment['selected'])
            continue
        attempt = dict(id=new_id(), text=segment['text'], status='running', started_at=time.time())
        segment['attempts'].append(attempt)
        segment['status'] = 'running'
        write_json(path, job)
        try:
            print(f'Generating segment {index+1}/{len(job["segments"])}', flush=True)
            with capture_normalized_text(engine) as normalized:
                chunks = list(engine.run(dict(text=segment['text'], text_lang=job.get('text_language', 'zh'), ref_audio_path=voice['reference'], prompt_text=voice['reference_text'],
                                          prompt_lang=voice['language'], text_split_method='cut0', batch_size=1, split_bucket=False,
                                          return_fragment=False, fragment_interval=job.get('synthesis', {}).get('fragment_interval', .3),
                                          speed_factor=job['speed'], seed=42, parallel_infer=True)))
            attempt['normalized_text'] = ''.join(normalized)
            attempt['normalization_source'] = 'synthesis_frontend'
            if not attempt['normalized_text'].strip():
                raise CastError('missing_normalization', 'Synthesis did not record its actual frontend text.')
            from castlib.textmap import normalization_map
            try:
                if segment.get('requested_mapping'):
                    from castlib.script_audio import compose_mapping
                    attempt['text_mapping'] = compose_mapping(segment['requested_mapping'],normalization_map(segment['spoken_text'],attempt['normalized_text']))
                else:
                    attempt['text_mapping'] = normalization_map(segment.get('display_text',segment['text']),attempt['normalized_text'])
            except CastError as mapping_error:
                attempt['mapping_error'] = dict(code=mapping_error.code,message=str(mapping_error))
            if not chunks or len({x[0] for x in chunks}) != 1:
                raise CastError('invalid_engine_output', 'No consistent audio returned.')
            rate = chunks[0][0]
            audio = np.concatenate([x[1] for x in chunks])
            if not audio.size or not np.isfinite(audio).all() or np.max(np.abs(audio)) == 0:
                raise CastError('invalid_engine_output', 'Engine returned empty or silent audio.')
            filename = 'segment-' + attempt['id'] + '.wav'
            temp = directory / (filename + '.tmp')
            sf.write(temp, audio, rate, subtype='PCM_16', format='WAV')
            os.replace(temp, directory / filename)
            info = wav_info(directory / filename)
            attempt.update(status='succeeded', file=filename, elapsed_seconds=time.time()-attempt['started_at'], **info)
            segment.update(status='succeeded', selected=filename)
            write_json(path, job)
        except Exception as exc:
            attempt.update(status='failed', error=str(exc))
            segment['status'] = 'failed'
            job.update(status='failed', error=str(exc))
            write_json(path, job)
            raise
    job['status'] = 'succeeded'
    write_json(path, job)
    state = root / 'features/voice.json'
    record = read_json(state)
    record['reference_inference_verified'] = True
    write_json(state, record)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--job')
    parser.add_argument('--reference-text')
    parser.add_argument('--language', default='zh')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.prepare:
        try:
            prepare(root, args.prepare, args.output, args.reference_text, args.language)
        except Exception as exc:
            write_json(args.output.with_suffix('.error.json'), dict(code=getattr(exc, 'code', 'reference_preparation_failed'), message=str(exc)))
            raise
    else:
        # Upstream is verbose; stdout here is a log, never the public CLI protocol.
        with contextlib.redirect_stdout(sys.stderr):
            model = read_json(item_path(root, 'jobs', args.job) / 'job.json')['model'].rsplit(':', 1)[-1] if args.job else 'v2Pro'
            engine = load_engine(root, model)
            if args.probe:
                from faster_whisper import WhisperModel
                WhisperModel(str(root / 'models/faster-whisper-small'), device='cpu', compute_type='int8', local_files_only=True)
            if args.job:
                process(root, args.job, engine)
        print('Model loaded successfully.' if args.probe else 'Job completed.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
