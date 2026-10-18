import copy
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'runtime/codoop-cast'))
from castlib.common import read_json, write_json
from castlib.research import validate_report, export_report


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.draft = self.root / 'draft'
        shutil.copytree(ROOT / 'examples/research-subtitle-timing', self.draft)
        self.file = self.draft / 'report.json'
        self.report = read_json(self.file)

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, fn):
        fn(self.report['data'])
        write_json(self.file, self.report)

    def test_export_is_portable_and_preserves_claim_identity(self):
        result = export_report(self.file, self.root / 'delivery')
        self.assertEqual(result['report_state'], 'ready')
        self.assertEqual(read_json(result['handoff']), self.report)
        shutil.rmtree(self.draft)
        self.assertEqual(validate_report(result['handoff'])['claims'], 2)
        text = Path(result['report']).read_text(encoding='utf-8')
        self.assertIn('https://developer.mozilla.org/', text)
        self.assertIn('发布日期：未知', text)

    def test_partial_unsupported_claim_stays_partial(self):
        self.edit(lambda d: (d.update(state='partial'), d['claims'][0].update(evidence_ids=[])))
        result = export_report(self.file, self.root / 'partial')
        self.assertEqual(result['report_state'], 'partial')
        self.assertEqual(result['unsupported_claim_ids'], ['claim-cue-times'])
        self.assertIn('资料尚不完整', Path(result['report']).read_text(encoding='utf-8'))

    def test_ready_claim_without_evidence_rejected(self):
        self.edit(lambda d: d['claims'][0].update(evidence_ids=[]))
        with self.assertRaisesRegex(ValueError, 'supported claims'):
            validate_report(self.file)

    def test_unread_search_metadata_cannot_support_claim(self):
        self.edit(lambda d: d['sources'][0].update(read_status='metadata'))
        with self.assertRaisesRegex(ValueError, 'Unread source'):
            validate_report(self.file)

    def test_stale_snapshot_rejected(self):
        (self.draft / 'sources/mdn-webvtt.md').write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            validate_report(self.file)

    def test_snapshot_escape_rejected(self):
        outside = self.root / 'outside.md'; outside.write_text('outside', encoding='utf-8')
        self.edit(lambda d: d['sources'][0].update(snapshot_path='../outside.md', snapshot_sha256=hashlib.sha256(outside.read_bytes()).hexdigest()))
        with self.assertRaisesRegex(ValueError, 'Unavailable local resource'):
            validate_report(self.file)

    def test_unknown_paragraph_claim_rejected(self):
        self.edit(lambda d: d['summary'].update(claim_ids=['missing']))
        with self.assertRaisesRegex(ValueError, 'Unknown paragraph claim'):
            validate_report(self.file)

    def test_unknown_evidence_rejected(self):
        self.edit(lambda d: d['claims'][0].update(evidence_ids=['missing']))
        with self.assertRaisesRegex(ValueError, 'Unknown claim evidence'):
            validate_report(self.file)

    def test_offline_local_material_supported(self):
        self.edit(lambda d: (d.update(mode='offline'), d['sources'][0].update(source_type='local', url=None)))
        result = export_report(self.file, self.root / 'offline')
        self.assertEqual(result['report_state'], 'ready')
        self.assertIn('](<sources/mdn-webvtt.md>)', Path(result['report']).read_text(encoding='utf-8'))

    def test_existing_output_preserved(self):
        output = self.root / 'delivery'; output.mkdir()
        marker = output / 'existing.txt'; marker.write_text('keep', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'new report output'):
            export_report(self.file, output)
        self.assertEqual(marker.read_text(encoding='utf-8'), 'keep')

    def test_conflict_cannot_link_missing_claim(self):
        self.edit(lambda d: d['conflicts'].append(dict(id='conflict-one', claim_ids=['claim-cue-times','missing'], description='contradiction')))
        with self.assertRaisesRegex(ValueError, 'two existing claims'):
            validate_report(self.file)


if __name__ == '__main__':
    unittest.main()
