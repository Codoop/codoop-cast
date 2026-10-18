"""Maintainer-only v2Pro punctuation and segmentation experiment."""
import argparse
import contextlib
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'))
from castlib.common import read_json, write_json, lock, root_path
from castlib.setup import environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--root', type=Path, help='Private shared data root')
    parser.add_argument('--comparison-file', type=Path, required=True, help='Existing voice comparison JSON')
    args = parser.parse_args()
    root = root_path(args.root)
    previous = read_json(args.comparison_file)
    voice = read_json(root / 'voices' / previous['voice_id'] / 'voice.json')
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.update(environment(root))
    import numpy as np
    import soundfile as sf
    from worker import load_engine
    from compare_voice import level_match
    text = previous['script']
    variants = [
        ('E', text, 'cut0', .3),
        ('F', text, 'cut0', .01),
        ('G', text, 'cut3', .15),
        ('H', text.replace('程序会自动处理参考片段和文字，不需要手动裁切，也不需要训练模型。',
                           '程序会自动处理参考片段和文字。你不需要手动裁切，也不需要训练模型。'), 'cut0', .15),
    ]
    report = dict(model='v2Pro', voice_id=voice['id'], samples={}, seed=42, speed_factor=1.)
    with lock(root, 'gpu-voice'), contextlib.redirect_stdout(sys.stderr):
        engine = load_engine(root, 'v2Pro')
        for label, script, split, interval in variants:
            print('Rendering pause variant ' + label, file=sys.stderr, flush=True)
            chunks = list(engine.run(dict(text=script, text_lang='zh', ref_audio_path=voice['reference'],
                prompt_text=voice['reference_text'], prompt_lang=voice['language'],
                text_split_method=split, fragment_interval=interval, batch_size=1, split_bucket=False,
                return_fragment=False, speed_factor=1., seed=42, parallel_infer=(split == 'cut0'))))
            rate = chunks[0][0]
            audio = np.concatenate([a for sr, a in chunks])
            if not audio.size or not np.isfinite(audio).all() or not np.any(audio):
                raise ValueError('Invalid audio')
            path = args.output / (label + '.wav')
            sf.write(path, audio, rate, subtype='PCM_16')
            # Locate quiet spans as diagnostics, not as a speech/word alignment.
            floating, _ = sf.read(path)
            width = max(1, round(rate * .01))
            rms = [float(np.sqrt(np.mean(floating[i:i+width] ** 2))) for i in range(0, len(floating), width)]
            spans, start = [], None
            for i, value in enumerate(rms + [1.]):
                if value < .003 and start is None:
                    start = i
                elif value >= .003 and start is not None:
                    if (i-start)*.01 >= .15:
                        spans.append([round(start*.01, 2), round(min(i*width, len(floating))/rate, 2)])
                    start = None
            report['samples'][label] = dict(path=str(path), text=script, split=split,
                fragment_interval=interval, parallel_infer=(split == 'cut0'), seconds=len(audio)/rate, quiet_spans=spans)
            write_json(args.output / 'comparison.json', report)
    level_match(report)
    write_json(args.output / 'comparison.json', report)


if __name__ == '__main__':
    main()
