from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'))
from castlib.common import CastError
from castlib.textmap import normalization_map,project_spans,combine_display_units
from worker import capture_normalized_text


class TextMapTests(unittest.TestCase):
    def test_dates_prices_acronyms_and_resolution(self):
        display='现在是2026年10月17日，预算99.5元，CPU和GPU输出1080P视频，字幕SRT。'
        spoken='现在是二零二六年十月十七日,预算九十九点五元,C P U和G P U输出幺零八零P视频,字幕S R T.'
        mapping=normalization_map(display,spoken)
        for raw,normalized in [('2026','二零二六'),('99.5','九十九点五'),('1080P','幺零八零')]:
            pos=spoken.index(normalized)
            span=project_spans(mapping,[(pos,pos+len(normalized))])[0]
            self.assertEqual(display[slice(*span)],raw)
        self.assertEqual(mapping['display_text'],display)

    def test_does_not_hide_unrelated_rewrites(self):
        for a,b in [('今天讲成本','今天讲隐私'),('CPU','GPU'),('不能漏字','不漏字')]:
            with self.assertRaises(CastError):
                normalization_map(a,b)

    def test_semantic_numeric_symbols_are_preserved(self):
        for display,spoken in [('-3.14','负三点一四'),('80%','百分之八十')]:
            mapping=normalization_map(display,spoken)
            span=project_spans(mapping,[(0,len(spoken))])[0]
            self.assertEqual(display[slice(*span)],display)

    def test_numbers_are_indivisible_display_groups(self):
        mapping=normalization_map('99.5','九十九点五')
        spans=project_spans(mapping,[(i,i+1) for i in range(5)])
        units=[dict(id=str(i),script_span=dict(paragraph_id='p',start=a,end=b),start_sample=i*100,end_sample=(i+1)*100) for i,(a,b) in enumerate(spans)]
        merged,groups=combine_display_units(units)
        self.assertEqual(len(merged),1)
        self.assertEqual(merged[0]['end_sample'],500)
        self.assertEqual(len(groups),4)

    def test_frontend_capture_calls_original_once_and_restores_on_failure(self):
        calls=[]
        def original(text):
            calls.append(text)
            return [dict(norm_text='九十九点五元')]
        engine=SimpleNamespace(text_preprocessor=SimpleNamespace(preprocess=original))
        with self.assertRaises(RuntimeError):
            with capture_normalized_text(engine) as captured:
                engine.text_preprocessor.preprocess('99.5元')
                self.assertEqual(captured,['九十九点五元'])
                raise RuntimeError('interrupted')
        self.assertIs(engine.text_preprocessor.preprocess,original)
        self.assertEqual(calls,['99.5元'])
