"""Maintainer validation of native Qwen forced alignment; no service or training."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import unicodedata

RUNTIME = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RUNTIME))
from castlib.textmap import normalization_map,project_spans,combine_display_units


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def kept(char):
    return unicodedata.category(char)[0] in 'LN' or char == "'"


def subtitle_text(text):
    """Hide trailing punctuation only; keep internal text and meaningful symbols."""
    text = text.rstrip()
    while text and (text[-1] in '，。！？；：、,.!?;:…—' or text[-1] in ('"',"'") or unicodedata.category(text[-1]) in ('Ps','Pe','Pi','Pf')):
        text = text[:-1].rstrip()
    return text


def map_tokens(text, tokens):
    positions = [i for i,char in enumerate(text) if kept(char)]
    cursor, spans = 0, []
    for token in tokens:
        cleaned = ''.join(c for c in token if kept(c))
        selected = positions[cursor:cursor+len(cleaned)]
        if not cleaned or ''.join(text[i] for i in selected) != cleaned:
            raise ValueError('Alignment token does not map to spoken text: '+token)
        spans.append((selected[0],selected[-1]+1))
        cursor += len(cleaned)
    if cursor != len(positions):
        raise ValueError('Unmapped trailing text')
    return spans


def merge_zero_duration_units(units, displays, rate):
    """Group uncertain characters; never invent their individual duration."""
    units = copy.deepcopy(units)
    merges = []
    index = 0
    while index < len(units):
        current = units[index]
        if current['start_sample'] != current['end_sample']:
            index += 1
            continue
        span = current['script_span']
        candidates = []
        for neighbor_index in (index-1, index+1):
            if not 0 <= neighbor_index < len(units):
                continue
            neighbor = units[neighbor_index]
            ns = neighbor['script_span']
            if ns['paragraph_id'] != span['paragraph_id'] or neighbor['start_sample'] >= neighbor['end_sample']:
                continue
            lo, hi = (ns['end'],span['start']) if neighbor_index < index else (span['end'],ns['start'])
            gap = current['start_sample']-neighbor['end_sample'] if neighbor_index < index else neighbor['start_sample']-current['end_sample']
            if lo == hi and 0 <= gap <= round(rate*.16):
                candidates.append((gap,neighbor_index))
        if not candidates:
            index += 1
            continue
        _, target_index = min(candidates)
        target = units[target_index]
        original = copy.deepcopy(current)
        target['script_span']['start'] = min(target['script_span']['start'],span['start'])
        target['script_span']['end'] = max(target['script_span']['end'],span['end'])
        target['start_sample'] = min(target['start_sample'],current['start_sample'])
        target['end_sample'] = max(target['end_sample'],current['end_sample'])
        merges.append(dict(code='grouped_zero_duration_character',original=original,group_id=target['id'],
                           note='仅组合单元有时间范围，该字没有独立可靠时间。'))
        units.pop(index)
        index = max(0,index-1)
    return units, merges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-dir', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-prefix',default='demo')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    resources = json.loads((RUNTIME / 'resources-alignment.json').read_text(encoding='utf-8'))
    for resource in resources['assets']:
        path = args.model / Path(resource['target']).name
        hasher = hashlib.sha256()
        with path.open('rb') as source:
            while block := source.read(1024*1024):
                hasher.update(block)
        if hasher.hexdigest() != resource['sha256']:
            raise ValueError('Model checksum mismatch: '+path.name)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    import torch
    import transformers
    from transformers import AutoProcessor, AutoModelForTokenClassification
    job = json.loads((args.job_dir / 'job.json').read_text(encoding='utf-8'))
    from castlib.script_audio import verify_script_job,remap_display_units
    source_script = verify_script_job(job)
    from .config import speech_language
    alignment_language = {'zh':'Chinese','en':'English'}[speech_language(job.get('language', 'zh'))]
    manifest = json.loads(Path(job['artifacts'][1]).read_text(encoding='utf-8'))
    rate, total = manifest['sample_rate'], manifest['total_samples']
    audio_file = Path(job['artifacts'][0])
    checks = dict(state='needs_review', sample_rate=rate, total_samples=total, seconds=total/rate,
        audio_sha256=hashlib.sha256(audio_file.read_bytes()).hexdigest(),
        engine='Qwen3-ForcedAligner-0.6B-hf', transformers=transformers.__version__, torch=torch.__version__,
        attention='sdpa', dtype='float16', issues=[], warnings=[], segments=[], subjective_sync_verified=False,
        model_revision=resources['revision'],
        note='强制对齐不验证漏读；上游解码含时间戳单调修复，保存原始预测供检查。')
    start = time.monotonic()
    processor = AutoProcessor.from_pretrained(str(args.model), local_files_only=True)
    model = AutoModelForTokenClassification.from_pretrained(str(args.model), dtype=torch.float16,
        device_map='cuda:0', attn_implementation='sdpa', local_files_only=True).eval()
    checks['load_seconds'] = time.monotonic()-start
    torch.cuda.reset_peak_memory_stats()
    units, raw_results = [], []
    displays, paragraphs = {}, []
    for index, (segment, boundary) in enumerate(zip(job['segments'], manifest['segments']), 1):
        if (args.output.parent/'cancel').exists():
            checks.update(state='cancelled',srt_exported=False)
            write(args.output/'checks.json',checks)
            return
        pid = f'p{index:03}'
        display = segment.get('display_text',segment['text'])
        spoken = boundary.get('normalized_text') or display
        if not boundary.get('normalized_text') and any(c.isascii() and c.isalnum() for c in display):
            raise ValueError('Legacy mixed-text audio has no recorded frontend normalization; regenerate this narration to capture it.')
        mapping = boundary.get('text_mapping') if source_script else normalization_map(display,spoken)
        if source_script and (not mapping or mapping['display_text']!=display or mapping['spoken_text']!=spoken):
            raise ValueError('Recorded frontend mapping differs from the pinned display/normalized text.')
        displays[pid] = display
        paragraphs.append(dict(id=pid,display_text=display,spoken_text=spoken,claim_ids=[]))
        print(f'Aligning segment {index}/{len(job["segments"])}', flush=True)
        audio, source_rate = sf.read(args.job_dir / segment['selected'], dtype='float32')
        if audio.ndim != 1 or source_rate != rate:
            raise ValueError('Expected original mono segment sample rate')
        import math
        common = math.gcd(source_rate, 16000)
        audio16 = resample_poly(audio, 16000//common, source_rate//common).astype(np.float32)
        tick = time.monotonic()
        inputs, words = processor.prepare_forced_aligner_inputs(audio=audio16, transcript=spoken, language=alignment_language)
        inputs = inputs.to(model.device, model.dtype)
        with torch.inference_mode():
            outputs = model(**inputs)
        timestamps = processor.decode_forced_alignment(logits=outputs.logits, input_ids=inputs['input_ids'],
            word_lists=words, timestamp_token_id=model.config.timestamp_token_id)[0]
        raw_ids = outputs.logits.argmax(-1)[0][inputs['input_ids'][0] == model.config.timestamp_token_id].cpu().tolist()
        raw_results.append(dict(paragraph_id=pid, decoded=timestamps, raw_timestamp_prediction_ids=raw_ids))
        if source_script:
            raw_results[-1].update(source_display_span=segment['display_span'],script_spans=segment['script_spans'])
        previous, matched = boundary['start_sample'], 0
        spans = map_tokens(spoken,[item['text'] for item in timestamps])
        display_spans = project_spans(mapping,spans)
        raw_results[-1]['text_mapping'] = mapping
        for item, (pos,end) in zip(timestamps,display_spans):
            token = item['text']
            lo = boundary['start_sample'] + round(float(item['start_time']) * rate)
            hi = boundary['start_sample'] + round(float(item['end_time']) * rate)
            uid = f'u{len(units)+1:04}'
            units.append(dict(id=uid, script_span=dict(paragraph_id=pid,start=pos,end=end),start_sample=lo,end_sample=hi))
            previous = hi
            matched += sum(kept(c) for c in token)
        checks['segments'].append(dict(paragraph_id=pid, tokens=len(timestamps), matched_characters=matched,
            expected_characters=sum(kept(c) for c in spoken), elapsed_seconds=time.monotonic()-tick))
        del outputs, inputs
        write(args.output / 'raw-alignment.json', raw_results)
    write(args.output / 'raw-units.json', units)
    units,checks['normalization_groups'] = combine_display_units(units)
    units, checks['warnings'] = merge_zero_duration_units(units,displays,rate)
    previous = 0
    for unit in units:
        if not previous <= unit['start_sample'] < unit['end_sample'] <= total:
            checks['issues'].append(dict(code='invalid_unit_time', unit_id=unit['id']))
        previous = unit['end_sample']
    import jieba
    word_boundaries = {pid:{end for word,start,end in jieba.tokenize(text)} for pid,text in displays.items()}
    cues, group = [], []

    def flush():
        if not group:
            return
        first, last = group[0], group[-1]
        pid = first['script_span']['paragraph_id']
        text = displays[pid]
        lo, hi = first['script_span']['start'], last['script_span']['end']
        while hi < len(text) and not kept(text[hi]):
            hi += 1
        cues.append(dict(id=f'cue{len(cues)+1:03}',text=text[lo:hi],unit_ids=[u['id'] for u in group],
            start_sample=first['start_sample'],end_sample=last['end_sample']))
        group.clear()

    for unit in units:
        if group:
            prev = group[-1]
            pid = unit['script_span']['paragraph_id']
            same = pid == prev['script_span']['paragraph_id']
            gap = unit['start_sample'] - prev['end_sample']
            separator = displays[pid][prev['script_span']['end']:unit['script_span']['start']] if same else ''
            count = sum(len(displays[u['script_span']['paragraph_id']][u['script_span']['start']:u['script_span']['end']]) for u in group)
            elapsed = (unit['end_sample'] - group[0]['start_sample'])/rate
            word_end = prev['script_span']['end'] in word_boundaries.get(pid,set())
            if not same or gap > .6*rate or (re.search('[，。！？；,.!?;]', separator) and count >= 5) or (count >= 16 and word_end) or elapsed > 5:
                carry=[]
                if same and not separator and len(group)>1:
                    last_span=group[-1]['script_span']
                    if displays[pid][last_span['start']:last_span['end']] in ('和','与','及','把','被'):
                        carry=[group.pop()]
                flush()
                group.extend(carry)
        group.append(unit)
    flush()
    by_id = {unit['id']:unit for unit in units}
    compact = []
    for cue in cues:
        if compact:
            prior = compact[-1]
            same = by_id[prior['unit_ids'][-1]]['script_span']['paragraph_id'] == by_id[cue['unit_ids'][0]]['script_span']['paragraph_id']
            short = cue['end_sample']-cue['start_sample'] < .7*rate or sum(kept(c) for c in cue['text']) <= 3
            if same and short and cue['start_sample']-prior['end_sample'] <= .25*rate and len(prior['text']+cue['text'])<=24 and cue['end_sample']-prior['start_sample']<=6*rate:
                prior['text'] += cue['text']
                prior['unit_ids'] += cue['unit_ids']
                prior['end_sample'] = cue['end_sample']
                continue
        compact.append(cue)
    cues = compact
    for index,cue in enumerate(cues,1):
        cue['id'] = f'cue{index:03}'
        cue['text'] = subtitle_text(cue['text'])
    expected_display=''.join(c for text in displays.values() for c in text if kept(c))
    actual_display=''.join(c for cue in cues for c in cue['text'] if kept(c))
    checks['display_coverage_exact'] = expected_display == actual_display
    if not checks['display_coverage_exact']:
        checks['issues'].append(dict(code='display_coverage_mismatch'))
    previous = 0
    for cue in cues:
        lo, hi = round(cue['start_sample']/rate*1000), round(cue['end_sample']/rate*1000)
        if not previous <= lo < hi <= round(total/rate*1000):
            checks['issues'].append(dict(code='invalid_srt_time',cue_id=cue['id']))
        if hi-lo < 450:
            checks['issues'].append(dict(code='short_cue',cue_id=cue['id'],milliseconds=hi-lo))
        previous = hi
    script_artifact = source_script or dict(schema_version='0.1.0',kind='script',artifact_id=args.artifact_prefix+'-script',revision=2,
        data=dict(language=job.get('language', 'zh'),provenance='实际TTS前端规范化与输入配音稿；历史纯中文可用输入文本回退。',paragraphs=paragraphs))
    script_ref = {key:script_artifact[key] for key in ('artifact_id','revision')}
    if source_script:
        units = remap_display_units(units,job['segments'])
        checks.update(script=script_ref,script_fingerprint=job['script_fingerprint'],paragraph_identity_preserved=True)
    alignment = dict(schema_version='0.1.0',kind='alignment',artifact_id=args.artifact_prefix+'-alignment',revision=2,
        data=dict(script=script_ref,audio=dict(artifact_id=args.artifact_prefix+'-audio',revision=1),span_basis='display_text',
                  state='needs_review' if checks['issues'] or checks['warnings'] else 'ready',timebase='audio_samples',units=units,cues=cues,
                  issues=[json.dumps(x,ensure_ascii=False) for x in checks['issues']+checks['warnings']]))
    write(args.output / 'alignment.json', alignment)
    write(args.output / 'script.json',script_artifact)
    media=args.output/'media'
    media.mkdir()
    shutil.copyfile(audio_file,media/'narration.wav')
    write(args.output/'audio.json',dict(schema_version='0.1.0',kind='audio',artifact_id=args.artifact_prefix+'-audio',revision=1,
        data=dict(script=script_ref,origin='Selected source audio; SHA-256 and engine details in checks.json',
            sample_rate=rate,total_samples=total,media_available=True,media_path='media/narration.wav',
            segments=[dict(id=f'audio{i:03}',start_sample=b['start_sample'],end_sample=b['end_sample'],
                spoken_text=b['spoken_text'] if source_script else p['spoken_text'],
                script_spans=b['script_spans'] if source_script else [dict(paragraph_id=p['id'],start=0,end=len(p['spoken_text']))],
                display_span=b['display_span'] if source_script else dict(paragraph_id=p['id'],start=0,end=len(p['display_text'])),
                normalized_text=b.get('normalized_text') or p['spoken_text'],text_mapping=b.get('text_mapping') or {})
                for i,(b,p) in enumerate(zip(manifest['segments'],paragraphs),1)])))
    def stamp(samples):
        ms = round(samples/rate*1000)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    if any(i['code'] in ('invalid_unit_time','invalid_srt_time','display_coverage_mismatch') for i in checks['issues']):
        checks['srt_exported'] = False
    else:
        (args.output / 'subtitles.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start_sample"])} --> {stamp(c["end_sample"])}\n{c["text"]}' for i,c in enumerate(cues,1))+'\n',encoding='utf-8')
        checks['srt_exported'] = True
    checks.update(total_units=len(units),total_cues=len(cues),peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved(),elapsed_seconds=time.monotonic()-start)
    write(args.output / 'checks.json',checks)
    print(json.dumps(checks,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
