import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'runtime/codoop-cast'))
from castlib import assets, project, produce
from castlib.common import CastError, read_json, write_json


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, CODOOP_CAST_HOME=str(self.root/'private'))
        self.env.start()
        self.source = self.root/'original.svg'
        self.source.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>', encoding='utf-8')
        self.manifest = self.root/'manifest.json'
        self.entry = dict(id='topic-overview', source_file='original.svg', origin='Agent-created SVG', usage_notes='Overview scene',
                          provenance=dict(source_type='code', creator='Host agent'))
        write_json(self.manifest, dict(items=[self.entry]))

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_portable_copy_and_provenance_survive_source_removal(self):
        result = assets.build(self.manifest, self.root/'collection')
        data = read_json(result['assets'])
        self.source.unlink()
        self.assertEqual(assets.validate(result['assets'])['items'], 1)
        self.assertEqual(data['data']['items'][0]['provenance'], self.entry['provenance'])
        self.assertTrue(data['data']['items'][0]['path'].startswith('media/'))

    def test_identical_content_reuses_one_file(self):
        second = dict(self.entry, id='another-use')
        write_json(self.manifest, dict(items=[self.entry, second]))
        result = assets.build(self.manifest, self.root/'collection')
        items = read_json(result['assets'])['data']['items']
        self.assertEqual(items[0]['path'], items[1]['path'])
        self.assertEqual(len(list((self.root/'collection/media').iterdir())), 1)

    def test_replacement_preserves_identity_and_old_bytes(self):
        first = assets.build(self.manifest, self.root/'v001')
        old = read_json(first['assets'])
        old_bytes = (self.root/'v001'/old['data']['items'][0]['path']).read_bytes()
        self.source.write_text('<svg>new content</svg>', encoding='utf-8')
        second = assets.build(self.manifest, self.root/'v002', first['assets'])
        new = read_json(second['assets'])
        self.assertEqual(new['artifact_id'], old['artifact_id'])
        self.assertEqual(new['revision'], 2)
        self.assertEqual(new['data']['items'][0]['id'], old['data']['items'][0]['id'])
        self.assertNotEqual(new['data']['items'][0]['sha256'], old['data']['items'][0]['sha256'])
        self.assertEqual((self.root/'v001'/old['data']['items'][0]['path']).read_bytes(), old_bytes)

    def test_missing_file_duplicate_id_and_expected_hash_fail_before_output(self):
        for entries in ([dict(self.entry, source_file='missing.png')], [self.entry, self.entry], [dict(self.entry, sha256='wrong')]):
            write_json(self.manifest, dict(items=entries))
            with self.assertRaises(CastError):
                assets.build(self.manifest, self.root/'output')
            self.assertFalse((self.root/'output').exists())

    def test_output_and_tampered_collection_are_rejected(self):
        result = assets.build(self.manifest, self.root/'collection')
        with self.assertRaises(CastError):
            assets.build(self.manifest, self.root/'collection')
        item = read_json(result['assets'])['data']['items'][0]
        (self.root/'collection'/item['path']).write_text('tampered')
        with self.assertRaisesRegex(CastError, 'hash mismatch'):
            assets.validate(result['assets'])

    def test_escaping_resource_is_rejected(self):
        result = assets.build(self.manifest, self.root/'collection')
        artifact = read_json(result['assets'])
        artifact['data']['items'][0]['path'] = '../original.svg'
        write_json(result['assets'], artifact)
        with self.assertRaisesRegex(CastError, 'escaping'):
            assets.validate(result['assets'])

    def test_empty_code_only_collection_is_complete(self):
        write_json(self.manifest, dict(items=[]))
        self.assertEqual(assets.build(self.manifest, self.root/'collection')['items'], 0)

    def test_attach_preserves_original_and_rejects_registered_or_conflicting_files(self):
        result = assets.build(self.manifest, self.root/'collection')
        package = self.root/'work'
        package.mkdir()
        attached = assets.attach(result['assets'], package)
        self.assertTrue(attached['index_required'])
        self.assertEqual(read_json(package/'assets.json'), read_json(result['assets']))
        self.assertEqual(assets.attach(result['assets'], package)['items'], 1)
        item = read_json(result['assets'])['data']['items'][0]
        (package/item['path']).write_text('different')
        with self.assertRaisesRegex(CastError, 'Conflicting'):
            assets.attach(result['assets'], package)
        write_json(package/'version.json', {})
        with self.assertRaisesRegex(CastError, 'immutable'):
            assets.attach(result['assets'], package)
        assets.validate(result['assets'])

    def test_visual_replacement_plan_reuses_audio(self):
        folder = self.root/'project'
        project.initialize(folder)
        for stage, deps in [('script', []), ('storyboard', ['script=v001']), ('assets', ['storyboard=v001']),
                            ('scenes', ['storyboard=v001', 'assets=v001']), ('voice', ['script=v001']), ('subtitles', ['voice=v001'])]:
            for filename in project.STAGES[stage]:
                path = folder/stage/'v001'/filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
            project.register(folder, stage, 'v001', deps)
            project.select(folder, stage, 'v001')
        run = produce.plan(folder, force=['assets'])
        steps = {step['stage']:step['action'] for step in read_json(run['plan'])['steps']}
        self.assertEqual(steps['storyboard'], 'reuse')
        self.assertEqual(steps['subtitles'], 'reuse')
        self.assertEqual(steps['assets'], 'build')
        self.assertEqual(steps['scenes'], 'build')
        self.assertNotIn('voice', steps)


if __name__ == '__main__':
    unittest.main()
