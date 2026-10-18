"""Stdlib adapter from stable script paragraphs to independently synthesized chunks."""
import copy
import hashlib
import json

from .common import CastError
from .textmap import normalization_map


def fingerprint(artifact):
    return hashlib.sha256(json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(value, message):
    if not value:
        raise CastError('invalid_script_audio', message)


def paragraph_mapping(paragraph):
    display, spoken = paragraph['display_text'], paragraph['spoken_text']
    overrides = paragraph.get('pronunciation_spans', [])
    if not overrides:
        return normalization_map(display, spoken)
    groups = []
    ds = ss = 0
    for item in [*overrides, dict(display_start=len(display), display_end=len(display), spoken_start=len(spoken), spoken_end=len(spoken))]:
        a, b, c, d = (item[k] for k in ('display_start', 'display_end', 'spoken_start', 'spoken_end'))
        require(ds <= a <= b <= len(display) and ss <= c <= d <= len(spoken), 'Pronunciation spans must be monotonic and within both texts.')
        left, right = display[ds:a], spoken[ss:c]
        if any(ch.isalnum() for ch in left + right):
            mapping = normalization_map(left, right)
            groups.extend(dict(display_start=g['display_start']+ds, display_end=g['display_end']+ds,
                               spoken_start=g['spoken_start']+ss, spoken_end=g['spoken_end']+ss, kind=g['kind']) for g in mapping['groups'])
        if a < b or c < d:
            require(a < b and c < d and any(ch.isalnum() for ch in display[a:b]) and any(ch.isalnum() for ch in spoken[c:d]), 'An override must map nonempty readable ranges.')
            groups.append(dict(display_start=a, display_end=b, spoken_start=c, spoken_end=d, kind='explicit_pronunciation'))
        ds, ss = b, d
    return dict(version=1, display_text=display, spoken_text=spoken, groups=groups)


def compose_mapping(first, second):
    require(first['spoken_text'] == second['display_text'], 'Pronunciation mapping does not match actual synthesis input.')
    groups = []
    for group in first['groups']:
        matches = [g for g in second['groups'] if g['display_start'] < group['spoken_end'] and g['display_end'] > group['spoken_start']]
        require(bool(matches), 'Actual frontend text no longer covers a pronunciation group.')
        groups.append(dict(display_start=group['display_start'], display_end=group['display_end'],
                           spoken_start=min(g['spoken_start'] for g in matches), spoken_end=max(g['spoken_end'] for g in matches), kind=group['kind']))
    return dict(version=1, display_text=first['display_text'], spoken_text=second['spoken_text'], groups=groups)


def prepare_script(artifact, limit=100):
    require(artifact.get('kind') == 'script' and artifact.get('schema_version') == '0.1.0'
            and isinstance(artifact.get('artifact_id'), str) and bool(artifact['artifact_id'])
            and isinstance(artifact.get('revision'), int) and artifact['revision'] > 0, 'Provide a supported script artifact.')
    paragraphs = artifact['data']['paragraphs']
    require(bool(paragraphs) and len({p['id'] for p in paragraphs}) == len(paragraphs), 'Script needs nonempty, unique paragraphs.')
    chunks = []
    for p in paragraphs:
        require(bool(p['id']) and all(isinstance(p[k], str) and any(ch.isalnum() for ch in p[k]) for k in ('display_text', 'spoken_text')), 'Paragraphs need readable display and spoken text.')
        mapping = paragraph_mapping(p)
        text = p['spoken_text']; start = display_start = 0
        while start < len(text):
            end = min(start + limit, len(text))
            if end < len(text):
                stops = [i+1 for i in range(start+limit//2, end) if text[i] in '。！？!?；;，,\n']
                if stops:
                    end = stops[-1]
                # Do not split a displayed token or explicit pronunciation.
                for group in mapping['groups']:
                    if group['spoken_start'] < end < group['spoken_end']:
                        end = group['spoken_end']
                if not any(ch.isalnum() for ch in text[end:]):
                    end = len(text)
            groups = [g for g in mapping['groups'] if start <= g['spoken_start'] and g['spoken_end'] <= end]
            require(bool(groups), 'Synthesis chunk has no mapped readable text.')
            following = [g['display_start'] for g in mapping['groups'] if g['spoken_start'] >= end]
            display_end = min(following) if following else len(p['display_text'])
            local = dict(version=1, display_text=p['display_text'][display_start:display_end], spoken_text=text[start:end],
                         groups=[dict(g, display_start=g['display_start']-display_start, display_end=g['display_end']-display_start,
                                      spoken_start=g['spoken_start']-start, spoken_end=g['spoken_end']-start) for g in groups])
            chunks.append(dict(spoken_text=text[start:end], display_text=local['display_text'], requested_mapping=local,
                               script_spans=[dict(paragraph_id=p['id'], start=start, end=end)],
                               display_span=dict(paragraph_id=p['id'], start=display_start, end=display_end)))
            start, display_start = end, display_end
    return chunks


def verify_script_job(job):
    artifact = job.get('script_artifact')
    if artifact is None:
        return None
    require(fingerprint(artifact) == job.get('script_fingerprint'), 'Pinned script changed after task creation.')
    expected = prepare_script(artifact)
    require(len(expected) == len(job['segments']), 'Script chunk count changed.')
    from .voice import narration_text
    for chunk, segment in zip(expected, job['segments']):
        require(all(segment.get(key) == value for key, value in chunk.items()), 'Synthesis chunk no longer matches the pinned script.')
        require(segment['text'] == narration_text(chunk['spoken_text']), 'Synthesis text changed; create a new script revision instead.')
    return artifact


def remap_display_units(units, segments):
    result = copy.deepcopy(units)
    for unit in result:
        span = unit['script_span']
        source = segments[int(span['paragraph_id'][1:])-1]['display_span']
        span.update(paragraph_id=source['paragraph_id'], start=span['start']+source['start'], end=span['end']+source['start'])
    return result
