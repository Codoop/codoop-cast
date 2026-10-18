import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_production import validate


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.package = Path(self.tmp.name) / 'package'
        shutil.copytree(ROOT / 'examples/72-second-workflow', self.package)

    def tearDown(self):
        self.tmp.cleanup()

    def change(self, kind, edit):
        path = self.package / (kind + '.json')
        artifact = json.loads(path.read_text(encoding='utf-8'))
        edit(artifact['data'])
        path.write_text(json.dumps(artifact, ensure_ascii=False), encoding='utf-8')
        index = self.package / 'package.json'
        manifest = json.loads(index.read_text(encoding='utf-8'))
        for entry in manifest['artifacts']:
            if entry['path'] == path.name:
                entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        index.write_text(json.dumps(manifest), encoding='utf-8')

    def test_pending_example_is_valid_but_not_renderable(self):
        self.assertFalse(validate(self.package)['render_ready'])

    def test_missing_revision_is_rejected(self):
        self.change('video-script', lambda d: d['script'].update(revision=99))
        with self.assertRaisesRegex(ValueError, 'Dangling'):
            validate(self.package)

    def test_wrong_reference_kind_is_rejected(self):
        self.change('video-script', lambda d: d['script'].update(artifact_id='demo-assets'))
        with self.assertRaisesRegex(ValueError, 'kind mismatch'):
            validate(self.package)

    def test_changed_spoken_text_invalidates_mapping(self):
        self.change('audio', lambda d: d['segments'][0].update(spoken_text='错误的稿件'))
        with self.assertRaisesRegex(ValueError, 'mapping differs'):
            validate(self.package)

    def test_cannot_claim_render_ready_without_dependencies(self):
        self.change('timeline', lambda d: d.update(state='ready', blockers=[]))
        with self.assertRaisesRegex(ValueError, 'not render-ready'):
            validate(self.package)

    def test_package_cannot_reference_files_outside_directory(self):
        path = self.package / 'package.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        manifest['artifacts'][0]['path'] = '../outside.json'
        path.write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'escapes'):
            validate(self.package)
