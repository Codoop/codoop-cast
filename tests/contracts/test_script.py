from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'runtime/codoop-cast'))
from castlib.common import digest, read_json, write_json
from castlib.script import validate_script, export_script
from authoring_worker import prepare


class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'research'
        shutil.copytree(ROOT / 'examples/research-subtitle-timing', self.source)
        self.report = self.source / 'report.json'
        self.script = self.root / 'draft.json'
        shutil.copyfile(ROOT / 'examples/script-subtitle-timing/script.json', self.script)

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, fn):
        artifact = read_json(self.script); fn(artifact['data']); write_json(self.script, artifact)

    def test_export_portable_preserves_ids_and_plain_narration(self):
        result = export_script(self.script, self.report, self.root / 'delivery', target_seconds=60)
        out = Path(result['package'])
        self.assertEqual(read_json(out / 'script.json'), read_json(self.script))
        shutil.rmtree(self.source)
        self.assertEqual(validate_script(out / 'script.json')['paragraphs'], 3)
        self.assertFalse((out / 'script.txt').read_text(encoding='utf-8').startswith('#'))
        self.assertIn('WebVTT', (out / 'script.txt').read_text(encoding='utf-8'))
        self.assertTrue(result['duration']['estimated'])
        self.assertEqual(result['duration']['target_seconds'], 60)

    def test_stale_report_revision_rejected(self):
        self.edit(lambda d: d['source'].update(revision=99))
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_script(self.script, self.report)

    def test_nonexistent_claim_rejected(self):
        self.edit(lambda d: d['paragraphs'][0].update(claim_ids=['missing']))
        with self.assertRaisesRegex(ValueError, 'valid claim'):
            validate_script(self.script, self.report)

    def test_empty_paragraph_rejected(self):
        self.edit(lambda d: d['paragraphs'][0].update(display_text=' '))
        with self.assertRaisesRegex(ValueError, 'empty'):
            validate_script(self.script, self.report)

    def test_duplicate_paragraph_id_rejected(self):
        self.edit(lambda d: d['paragraphs'][1].update(id=d['paragraphs'][0]['id']))
        with self.assertRaisesRegex(ValueError, 'Duplicate paragraph'):
            validate_script(self.script, self.report)

    def test_external_input_remains_unverified(self):
        external = self.root / 'source.md'; external.write_text('用户提供的报告，未独立验证。', encoding='utf-8')
        self.edit(lambda d: (d.update(source=dict(kind='external', sha256=digest(external))), [p.update(claim_ids=[]) for p in d['paragraphs']]))
        result = export_script(self.script, external, self.root / 'external')
        self.assertEqual(result['source_state'], 'unverified')
        self.assertTrue(result['warnings'])

    def test_external_input_cannot_invent_claim_ids(self):
        external = self.root / 'source.txt'; external.write_text('some report', encoding='utf-8')
        self.edit(lambda d: d.update(source=dict(kind='external', sha256=digest(external))))
        with self.assertRaisesRegex(ValueError, 'must not invent'):
            validate_script(self.script, external)

    def test_changed_retained_source_rejected(self):
        export_script(self.script, self.report, self.root / 'delivery')
        p = self.root / 'delivery/inputs/report.json'; p.write_text(p.read_text(encoding='utf-8') + ' ', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Retained report changed'):
            validate_script(self.root / 'delivery/script.json')

    def test_partial_research_not_promoted_to_verified(self):
        report = read_json(self.report); report['data']['state'] = 'partial'; write_json(self.report, report)
        result = validate_script(self.script, self.report)
        self.assertEqual(result['source_state'], 'partial')
        self.assertTrue(any('partial' in w for w in result['warnings']))

    def test_storyboard_import_keeps_script_identity_and_paragraph_ids(self):
        result = export_script(self.script, self.report, self.root / 'delivery')
        prepare(dict(script_file=result['handoff'], output=str(self.root / 'storyboard')))
        self.assertEqual(read_json(self.root / 'storyboard/script.json'), read_json(self.script))

    def test_existing_output_is_preserved(self):
        export_script(self.script, self.report, self.root / 'delivery')
        with self.assertRaisesRegex(ValueError, 'new script output'):
            export_script(self.script, self.report, self.root / 'delivery')

    def test_invalid_duration_assumptions_rejected(self):
        for rate in (0, float('nan'), float('inf')):
            with self.assertRaisesRegex(ValueError, 'positive and finite'):
                validate_script(self.script, self.report, characters_per_second=rate)
        with self.assertRaisesRegex(ValueError, 'Target seconds'):
            validate_script(self.script, self.report, target_seconds=-1)


if __name__ == '__main__':
    unittest.main()
