"""Monotonic mappings from actual TTS normalization back to display text."""
from difflib import SequenceMatcher
import re
import unicodedata

from .common import CastError


def kept(char):
    return unicodedata.category(char)[0] in 'LN' or char == "'"


def normalization_map(display, spoken):
    left = [i for i,c in enumerate(display) if kept(c)]
    right = [i for i,c in enumerate(spoken) if kept(c)]
    a, b = ''.join(display[i] for i in left), ''.join(spoken[i] for i in right)
    if not a or not b:
        raise CastError('empty_normalization', 'Text normalization has no readable content.')
    result = []
    numeral_chars = set('零〇一二两三四五六七八九十百千万亿兆点幺负正百分之年月日号第')
    for tag,i,j,k,l in SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if tag == 'equal':
            result.extend(dict(display_start=left[x],display_end=left[x]+1,
                               spoken_start=right[y],spoken_end=right[y]+1,kind='exact')
                          for x,y in zip(range(i,j),range(k,l)))
        elif tag == 'replace' and a[i:j].isascii() and a[i:j].isdigit() and set(b[k:l]) <= numeral_chars:
            result.append(dict(display_start=left[i],display_end=left[j-1]+1,
                               spoken_start=right[k],spoken_end=right[l-1]+1,kind='number_group'))
        else:
            raise CastError('unmapped_normalization', 'Actual TTS normalization needs review: '+repr(a[i:j])+' -> '+repr(b[k:l]))
    # A displayed acronym is indivisible even when TTS pronounces its letters
    # separately with long pauses. Numbers likewise retain their written form.
    for match in re.finditer(r'[A-Za-z][A-Za-z0-9]*|[¥￥$€£]?[-+]?[0-9]+(?:[.,][0-9]+)*(?:[A-Za-z]+)?[%％‰]?',display):
        if len(match.group()) < 2:
            continue
        members = [g for g in result if g['display_start'] < match.end() and g['display_end'] > match.start()]
        if not members:
            continue
        if any(g['display_start'] < match.start() or g['display_end'] > match.end() for g in members):
            raise CastError('ambiguous_normalization','Normalization crosses a display token boundary.')
        combined = dict(display_start=match.start(),display_end=match.end(),
            spoken_start=min(g['spoken_start'] for g in members),spoken_end=max(g['spoken_end'] for g in members),kind='display_token_group')
        result = [g for g in result if g not in members] + [combined]
    result.sort(key=lambda g:g['spoken_start'])
    return dict(version=1,display_text=display,spoken_text=spoken,groups=result)


def project_spans(mapping, spans):
    """Project normalized token spans; changed numbers stay indivisible groups."""
    result = []
    for start,end in spans:
        groups = [g for g in mapping['groups'] if g['spoken_start'] < end and g['spoken_end'] > start]
        if not groups:
            raise CastError('unmapped_token', 'Aligned token has no display mapping.')
        result.append((min(g['display_start'] for g in groups),max(g['display_end'] for g in groups)))
    return result


def combine_display_units(units):
    """Merge overlapping display spans, e.g. many spoken characters for 99.5."""
    import copy
    result, grouped = [], []
    for raw in units:
        unit = copy.deepcopy(raw)
        if result:
            prior = result[-1]
            a,b = prior['script_span'],unit['script_span']
            if a['paragraph_id'] == b['paragraph_id'] and b['start'] < a['end']:
                if b['start'] < a['start'] or unit['start_sample'] < prior['start_sample']:
                    raise CastError('nonmonotonic_mapping', 'Display mapping or audio timestamps are not monotonic.')
                a['end'] = max(a['end'],b['end'])
                prior['end_sample'] = max(prior['end_sample'],unit['end_sample'])
                grouped.append(dict(unit_id=unit['id'],group_id=prior['id'],reason='normalized_display_group'))
                continue
        result.append(unit)
    return result,grouped
