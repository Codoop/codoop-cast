"""Maintainer experiment: controlled reference/model comparison, no default changes.

Run with the private voice interpreter. Results do not change saved voice profiles.
"""
import argparse
import contextlib
import gc
import os
from pathlib import Path
import sys
import time

RUNTIME = Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'
sys.path.insert(0, str(RUNTIME))
from castlib.common import CastError, digest, item_path, lock, read_json, root_path, write_json
from castlib.reference import choose_reference
from castlib.setup import download, environment


def prepare_resources(root):
    manifest = read_json(RUNTIME / 'resources-voice-comparison.json')
    for asset in manifest['assets']:
        print('Preparing optional inference resource: ' + asset['target'], file=sys.stderr, flush=True)
        download(asset['url'], root / asset['target'], asset['sha256'], asset['size'])


def alternative_reference(voice, source, output):
    import imageio_ffmpeg
    import soundfile as sf
    import subprocess
    from opencc import OpenCC
    transcript = read_json(Path(voice['reference']).with_name('transcription.json'))
    original = Path(voice['original'])
    if digest(original) != digest(source):
        raise CastError('source_mismatch', 'Source must be the original used for this voice.')
    duration = voice['selection']['source_duration_seconds']
    a_start, a_end = voice['selection']['start_seconds'], voice['selection']['end_seconds']
    candidates = []
    for segment in transcript['segments']:
        try:
            candidate = choose_reference([segment], duration)
        except CastError:
            continue
        if candidate['needs_confirmation']:
            continue
        if candidate['start_seconds'] < a_end and candidate['end_seconds'] > a_start:
            continue
        if any(c.isascii() and c.isalpha() for c in candidate['text']):
            continue
        candidates.append(candidate)
    if not candidates:
        raise CastError('no_alternative', 'No independently usable second reference excerpt.')
    # This experiment deliberately tests a longer excerpt; it does not assume
    # duration predicts similarity or change the production selector.
    chosen = min(candidates, key=lambda c: abs(c['end_seconds']-c['start_seconds']-7.5))
    chosen['text'] = OpenCC('t2s').convert(chosen['text'])
    clip = output / 'reference-B.wav'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-y', '-i', str(source),
                    '-ss', str(chosen['start_seconds']), '-t', str(chosen['end_seconds']-chosen['start_seconds']),
                    '-ac', '1', '-ar', '32000', '-c:a', 'pcm_s16le', str(clip)], check=True)
    info = sf.info(clip)
    if not 3 <= info.duration <= 10:
        raise CastError('invalid_reference', 'Alternative clip violates model constraints.')
    return dict(reference=str(clip), reference_text=chosen['text'], language=voice['language'], selection=chosen)


def render(engine, voice, text, path):
    import numpy as np
    import soundfile as sf
    started = time.monotonic()
    chunks = list(engine.run(dict(text=text, text_lang='zh', ref_audio_path=voice['reference'],
                      prompt_text=voice['reference_text'], prompt_lang=voice['language'],
                      text_split_method='cut0', batch_size=1, split_bucket=False,
                      return_fragment=False, speed_factor=1., seed=42, parallel_infer=True)))
    if not chunks or len({sr for sr, _ in chunks}) != 1:
        raise CastError('invalid_audio', 'No consistent output from comparison model.')
    audio = np.concatenate([x[1] for x in chunks])
    if not audio.size or not np.isfinite(audio).all() or not np.any(audio):
        raise CastError('invalid_audio', 'Comparison returned empty or invalid audio.')
    sr = chunks[0][0]
    sf.write(path, audio, sr, subtype='PCM_16')
    return dict(path=str(path), seconds=len(audio)/sr, sample_rate=sr, elapsed_seconds=time.monotonic()-started,
                reference=voice['reference'], reference_text=voice['reference_text'])


def level_match(report):
    """RMS-match listening copies without changing pitch, speed or raw output."""
    import numpy as np
    import soundfile as sf
    loaded = {}
    target_rms = .06
    for label, sample in report['samples'].items():
        audio, rate = sf.read(sample['path'])
        rms = float(np.sqrt(np.mean(audio * audio)))
        peak = float(np.max(np.abs(audio)))
        if not rms or not np.isfinite(audio).all():
            raise CastError('invalid_audio', 'Cannot level-match an invalid comparison output.')
        target_rms = min(target_rms, .95 * rms / peak)
        loaded[label] = audio, rate, rms
    for label, (audio, rate, rms) in loaded.items():
        sample = report['samples'][label]
        path = Path(sample['path']).with_name(label + '-listen.wav')
        sf.write(path, audio * (target_rms / rms), rate, subtype='PCM_16')
        sample.update(listening_path=str(path), listening_gain=target_rms / rms)
    report['listening_target_rms'] = target_rms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root')
    parser.add_argument('--voice', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = root_path(args.root)
    source = args.source.resolve()
    script = args.script.resolve().read_text(encoding='utf-8-sig').strip()
    output = args.output.resolve()
    if not script or len(script) > 300:
        raise CastError('invalid_script', 'Use a nonempty short common comparison script (up to 300 characters).')
    if output.exists():
        raise CastError('output_exists', 'Use a new comparison output directory to preserve earlier results.')
    output.mkdir(parents=True)
    os.environ.update(environment(root))
    voice = read_json(item_path(root, 'voices', args.voice) / 'voice.json')
    if digest(voice['reference']) != voice['reference_sha256']:
        raise CastError('reference_changed', 'Saved reference changed.')
    alternative = alternative_reference(voice, source, output)
    import shutil
    shutil.copyfile(voice['reference'], output / 'reference-A.wav')
    report = dict(voice_id=voice['id'], script=script, source_sha256=digest(source), alternative=alternative,
                  parameters={'seed': 42, 'speed_factor': 1., 'top_k': 5, 'top_p': 1., 'temperature': 1.}, samples={})
    write_json(output / 'comparison.json', report)
    prepare_resources(root)
    import torch
    from worker import load_engine
    with lock(root, 'gpu-voice'):
        for model in ('v2', 'v2Pro', 'v2ProPlus'):
            with contextlib.redirect_stdout(sys.stderr):
                engine = load_engine(root, model)
                variants = [('A', voice), ('B', alternative)] if model == 'v2' else [('C' if model == 'v2Pro' else 'D', voice)]
                for label, reference in variants:
                    print(f'Comparison {label}: {model}', file=sys.stderr, flush=True)
                    sample = render(engine, reference, script, output / (label + '.wav'))
                    sample['model'] = model
                    report['samples'][label] = sample
                    write_json(output / 'comparison.json', report)
                del engine
                gc.collect()
                torch.cuda.empty_cache()
    level_match(report)
    write_json(output / 'comparison.json', report)
    print('Comparison completed: ' + str(output))


if __name__ == '__main__':
    main()
