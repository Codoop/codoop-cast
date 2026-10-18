"""Private alignment interpreter entrypoint, no HTTP service."""
import os
from pathlib import Path
import sys

os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')

if '--prepare' in sys.argv:
    import argparse
    import subprocess
    import json
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        import imageio_ffmpeg
        import soundfile as sf
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-n','-i',str(args.prepare),'-ac','1','-ar','32000','-c:a','pcm_s16le',str(args.output)],check=True)
        info=sf.info(args.output)
        if not 0 < info.duration <= 300:
            raise ValueError('External audio longer than five minutes needs automatic windowing, which is not yet implemented. The source is preserved.')
    except Exception as exc:
        args.output.with_suffix('.error.json').write_text(json.dumps(dict(code='external_audio_preparation',message=str(exc))),encoding='utf-8')
        raise
elif '--probe' in sys.argv:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--model',type=Path,required=True)
    args = parser.parse_args()
    import torch
    from transformers import AutoProcessor,AutoModelForTokenClassification
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable in private alignment environment')
    processor=AutoProcessor.from_pretrained(str(args.model),local_files_only=True)
    model=AutoModelForTokenClassification.from_pretrained(str(args.model),dtype=torch.float16,
        device_map='cuda:0',attn_implementation='sdpa',local_files_only=True).eval()
    print('Alignment model loaded successfully.')
else:
    from castlib.alignment_engine import main
    main()
