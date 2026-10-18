from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'runtime/codoop-cast'))
from castlib import data_layout
from castlib.common import CastError, read_json, write_json
from castlib.setup import environment


class SharedDataLayoutTests(unittest.TestCase):
    def test_inspection_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'missing'
            state = data_layout.inspect(root)
            self.assertFalse(state['registered'])
            self.assertFalse(root.exists())

    def test_register_existing_root_preserves_payloads_and_unknown_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(root/'voices/profile/voice.json', {'existing': True})
            write_json(root/'config.json', {'schema_version':1, 'output_language':'zh-CN'})
            (root/'personal-note.txt').write_text('keep')
            before = {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            data_layout.initialize(root)
            first = (root/data_layout.MARKER).read_bytes()
            data_layout.initialize(root)
            self.assertEqual(first, (root/data_layout.MARKER).read_bytes())
            for name, content in before.items():
                self.assertEqual((root/name).read_bytes(), content)
            self.assertEqual(data_layout.inspect(root)['unmanaged_entries'], ['personal-note.txt'])
            self.assertFalse((root/'envs').exists())
            self.assertFalse((root/'models').exists())

    def test_future_layout_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(root/data_layout.MARKER, {'kind':'cast-data-layout', 'schema_version':999})
            before = (root/data_layout.MARKER).read_bytes()
            with self.assertRaises(CastError):
                data_layout.initialize(root)
            self.assertEqual(before, (root/data_layout.MARKER).read_bytes())

    def test_child_process_temp_and_private_python_share_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = environment(root)
            self.assertEqual(env['TEMP'], str(root/'cache/tmp'))
            self.assertEqual(env['TMP'], env['TEMP'])
            self.assertTrue(Path(env['TEMP']).is_dir())
            self.assertEqual(env['UV_PYTHON_INSTALL_DIR'], str(root/'python'))
