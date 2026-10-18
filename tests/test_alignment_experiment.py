from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from align_experiment import map_tokens, merge_zero_duration_units


class AlignmentExperimentTests(unittest.TestCase):
    def test_numeric_punctuation_maps_to_original_range(self):
        text = '预算99.5元，GPU。'
        spans = map_tokens(text, ['预','算','995','元','GPU'])
        self.assertEqual(text[slice(*spans[2])], '99.5')
        self.assertEqual(text[slice(*spans[-1])], 'GPU')

    def test_missing_and_changed_words_are_not_silently_skipped(self):
        with self.assertRaises(ValueError):
            map_tokens('不能漏字', ['不','漏','字'])
        with self.assertRaises(ValueError):
            map_tokens('不能漏字', ['不','能','漏'])

    def test_zero_duration_group_preserves_text_and_observed_bounds(self):
        units = [dict(id='a',script_span=dict(paragraph_id='p',start=0,end=1),start_sample=0,end_sample=1600),
                 dict(id='b',script_span=dict(paragraph_id='p',start=1,end=2),start_sample=1600,end_sample=1600)]
        merged, warnings = merge_zero_duration_units(units,{'p':'今天'},16000)
        self.assertEqual(len(merged),1)
        self.assertEqual(merged[0]['script_span']['end'],2)
        self.assertEqual((merged[0]['start_sample'],merged[0]['end_sample']),(0,1600))
        self.assertEqual(len(warnings),1)
        self.assertEqual(len(units),2)  # raw evidence remains untouched

    def test_uncertain_token_across_pause_remains_unresolved(self):
        units = [dict(id='a',script_span=dict(paragraph_id='p',start=0,end=1),start_sample=0,end_sample=1600),
                 dict(id='b',script_span=dict(paragraph_id='p',start=1,end=2),start_sample=10000,end_sample=10000)]
        merged, warnings = merge_zero_duration_units(units,{'p':'今天'},16000)
        self.assertEqual(len(merged),2)
        self.assertEqual(warnings,[])
