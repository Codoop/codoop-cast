from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'runtime/codoop-cast'))
from castlib.common import read_json, write_json
from castlib.research import render_report, export_report
from castlib.script import export_script, load_source
from authoring_worker import prepare


class LanguageExportTests(unittest.TestCase):
    def test_english_report_labels_and_declared_language_survive_export(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            shutil.copytree(ROOT/'examples/research-subtitle-timing', folder/'input')
            path = folder/'input/report.json'
            report = read_json(path)
            report['data']['language'] = 'en'
            write_json(path, report)
            result = export_report(path, folder/'output')
            text = Path(result['report']).read_text(encoding='utf-8')
            self.assertIn('## Sources and access', text)
            self.assertIn('Published: Unknown', text)
            self.assertNotIn('来源与读取情况', text)
            self.assertEqual(read_json(result['handoff'])['data']['language'], 'en')

    def test_english_script_labels_preserve_source_and_paragraph_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder/'report.txt'
            source.write_text('A short source report.', encoding='utf-8')
            artifact = read_json(ROOT/'examples/script-subtitle-timing/script.json')
            data = artifact['data']
            data['language'] = 'en-US'
            data['source'] = load_source(source)[0]
            for paragraph in data['paragraphs']:
                paragraph.update(display_text='Read the source before writing.', spoken_text='Read the source before writing.', claim_ids=[])
            path = folder/'draft.json'
            write_json(path, artifact)
            result = export_script(path, source, folder/'output', target_seconds=30)
            text = Path(result['script']).read_text(encoding='utf-8')
            self.assertIn('# Narration script', text)
            self.assertIn('Target duration: 30 seconds.', text)
            self.assertFalse(any('\u4e00' <= c <= '\u9fff' for c in text))
            self.assertEqual(read_json(result['handoff']), artifact)

    def test_plain_text_prepare_pins_explicit_language(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder/'narration.txt'
            source.write_text('A short English narration.', encoding='utf-8')
            prepare(dict(text_file=str(source), output=str(folder/'output'), language='en'))
            self.assertEqual(read_json(folder/'output/script.json')['data']['language'], 'en')
