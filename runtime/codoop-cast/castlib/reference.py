"""Reference selection policy; timestamps are always tied to the selected text."""
import math

from .common import CastError

PUNCTUATION = '。！？.!?，,；;：:'


def choose_reference(segments, duration):
    """Choose a bounded utterance, preferring complete ASR segments/sentences.

    Confidence gates are conservative heuristics, not speaker verification.
    Words are a fallback only at punctuation boundaries, never a fixed-time cut.
    """
    candidates = []

    def add(start, end, text, probability, logprob, no_speech, kind):
        start, end = max(0, start - .10), min(duration, end + .15)
        length = end - start
        if not (3.05 <= length <= 9.75) or not text.strip() or not any(c.isalnum() for c in text):
            return
        values = (start, end, probability, logprob, no_speech)
        if not all(math.isfinite(x) for x in values):
            return
        confident = probability >= .65 and logprob >= -.8 and no_speech <= .5
        score = 2 * probability + logprob - no_speech - .04 * abs(length - 6.5)
        # In otherwise Chinese speech, names/acronyms are often confidently
        # mistranscribed. Prefer an equally clear ordinary-language excerpt.
        if any('\u4e00' <= c <= '\u9fff' for c in text) and any(c.isascii() and c.isalpha() for c in text):
            score -= .2
        if text.rstrip().endswith(tuple('。！？.!?')):
            score += .2
        candidates.append(dict(start_seconds=round(start, 4), end_seconds=round(end, 4),
                               text=text.strip(), confidence=probability, avg_logprob=logprob,
                               no_speech_prob=no_speech, selection=kind,
                               needs_confirmation=not confident, score=score))

    for i, first in enumerate(segments):
        group = []
        for segment in segments[i:]:
            if group and segment['start'] - group[-1]['end'] > .8:
                break
            group.append(segment)
            if segment['end'] - first['start'] > 9.5:
                break
            words = [word for s in group for word in s.get('words', [])]
            if not words:
                continue
            probability = sum(w['probability'] for w in words) / len(words)
            add(words[0]['start'], words[-1]['end'], ''.join(s['text'] for s in group), probability,
                min(s['avg_logprob'] for s in group), max(s['no_speech_prob'] for s in group), 'utterance')

        words = first.get('words', [])
        for a, word in enumerate(words):
            if a and not words[a-1]['word'].rstrip().endswith(tuple(PUNCTUATION)):
                continue
            for b in range(a, len(words)):
                if words[b]['end'] - word['start'] > 9.5:
                    break
                if b < len(words)-1 and not words[b]['word'].rstrip().endswith(tuple(PUNCTUATION)):
                    continue
                span = words[a:b+1]
                add(word['start'], words[b]['end'], ''.join(w['word'] for w in span),
                    sum(w['probability'] for w in span)/len(span), first['avg_logprob'],
                    first['no_speech_prob'], 'punctuated_words')

    if not candidates:
        raise CastError('no_reference_utterance', 'No complete, usable reference utterance was found. Supply clearer single-speaker audio; manual cutting is not required.')
    best = max(candidates, key=lambda x: (not x['needs_confirmation'], x['score']))
    best.pop('score')
    best['speaker_check'] = 'not_performed'
    return best
