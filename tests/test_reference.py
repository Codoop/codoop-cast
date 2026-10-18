from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'))
from castlib.common import CastError, new_id, write_json, digest
from castlib.reference import choose_reference
from castlib.voice import confirm_voice, list_voices


def segment(start, end, text, probability=.95, logprob=-.1):
    return dict(start=start, end=end, text=text, avg_logprob=logprob, no_speech_prob=.01,
                words=[dict(start=start, end=end, word=text, probability=probability)])


class ReferenceTests(unittest.TestCase):
    def test_long_source_returns_bounded_clip_with_its_own_text(self):
        segments = [segment(1, 7, '第一句完整的话。'), segment(30, 37, '另一句完整的话。')]
        selected = choose_reference(segments, 108)
        self.assertIn(selected['text'], [s['text'] for s in segments])
        self.assertGreaterEqual(selected['end_seconds']-selected['start_seconds'], 3)
        self.assertLessEqual(selected['end_seconds']-selected['start_seconds'], 10)
        self.assertFalse(selected['needs_confirmation'])

    def test_confident_speech_beats_uncertain_utterance(self):
        selected = choose_reference([segment(0, 6, '不清楚。', .3, -1.5), segment(20, 26, '清楚的句子。')], 40)
        self.assertEqual(selected['text'], '清楚的句子。')

    def test_uncertain_transcript_requests_confirmation(self):
        self.assertTrue(choose_reference([segment(1, 7, '待确认。', .4)], 20)['needs_confirmation'])

    def test_prefers_plain_chinese_over_ambiguous_acronyms(self):
        selected = choose_reference([segment(1, 7, '跳转到IS。'), segment(20, 26, '打开这个功能。')], 30)
        self.assertEqual(selected['text'], '打开这个功能。')

    def test_long_utterance_splits_only_on_word_punctuation_boundaries(self):
        s = segment(1, 17, '第一句话。第二句话。')
        s['words'] = [dict(start=1, end=8, word='第一句话。', probability=.9),
                      dict(start=9, end=17, word='第二句话。', probability=.9)]
        selected = choose_reference([s], 30)
        self.assertIn(selected['text'], ['第一句话。', '第二句话。'])

    def test_no_fake_padding_for_insufficient_speech(self):
        for segments in ([], [segment(0, 1, '短句。')]):
            with self.assertRaises(CastError):
                choose_reference(segments, 100)

    def test_draft_is_not_selectable_until_confirmed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ident = new_id()
            directory = root / 'voices' / ident
            directory.mkdir(parents=True)
            clip = directory / 'reference.wav'
            clip.write_bytes(b'example selected clip')
            write_json(directory / 'draft.json', dict(id=ident, reference=str(clip), reference_sha256=digest(clip),
                       reference_text='待确认', selection={'needs_confirmation': True}))
            self.assertEqual(list_voices(root), [])
            result = confirm_voice(root, ident, '已确认文字')
            self.assertEqual(result['voice']['reference_text'], '已确认文字')
            self.assertEqual(len(list_voices(root)), 1)


if __name__ == '__main__':
    unittest.main()
