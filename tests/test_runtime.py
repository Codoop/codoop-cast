import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
import zipfile

RUNTIME = Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'
sys.path.insert(0, str(RUNTIME))
from castlib.common import CastError, digest, item_path, lock, new_id, read_json, write_json
from castlib.setup import download, extract, setup
from castlib.voice import export_job, list_voices, select_voice, split_text, narration_text


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cast test 中文 ')
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exports_exact_samples_and_preserves_selected_audio(self):
        ident = new_id()
        directory = item_path(self.root, 'jobs', ident)
        directory.mkdir(parents=True)
        segments = []
        for index, samples in enumerate((1600, 3200)):
            filename = f'{index}.wav'
            with wave.open(str(directory / filename), 'wb') as out:
                out.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                out.writeframes(b'\x01\x00' * samples)
            segments.append(dict(id=new_id(), text='中文', selected=filename))
        hashes = [digest(directory / s['selected']) for s in segments]
        job = dict(id=ident, voice={'id': 'test'}, segments=segments)
        result = export_job(self.root, job)
        manifest = read_json(result['artifacts'][1])
        self.assertEqual(manifest['total_samples'], 8000)  # 1600 + 3200 pause + 3200
        self.assertEqual(manifest['segments'][1]['start_sample'], 4800)
        with wave.open(result['artifacts'][0]) as audio:
            self.assertEqual(audio.getnframes(), manifest['total_samples'])
        self.assertEqual(hashes, [digest(directory / s['selected']) for s in segments])
        existing = self.root / 'existing.wav'
        existing.write_bytes(b'preserve existing user file')
        with self.assertRaises(CastError):
            export_job(self.root, job, existing)
        self.assertEqual(existing.read_bytes(), b'preserve existing user file')

    def test_rejects_incomplete_export_and_existing_destination(self):
        job = dict(id=new_id(), segments=[{'selected': None}])
        with self.assertRaises(CastError):
            export_job(self.root, job)

    def test_pause_hints_preserve_words_numbers_and_original(self):
        import re
        text = '程序会自动处理参考片段和文字，不需要手动裁切，也不需要训练模型。价格是3.14元，版本v2Pro；请保留这些内容。'
        spoken = narration_text(text)
        self.assertIn('文字。', spoken)
        self.assertIn('3.14', spoken)
        self.assertEqual(re.sub(r'[^\w]', '', text), re.sub(r'[^\w]', '', spoken))
        self.assertEqual(narration_text('你好，欢迎回来。'), '你好，欢迎回来。')
        self.assertEqual(narration_text(spoken), spoken)

    def test_new_jobs_do_not_stack_join_silence(self):
        ident = new_id()
        directory = item_path(self.root, 'jobs', ident)
        directory.mkdir(parents=True)
        segments = []
        for index in range(2):
            name = str(index) + '.wav'
            with wave.open(str(directory / name), 'wb') as out:
                out.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                out.writeframes(b'\x01\x00' * 1600)
            segments.append(dict(id=new_id(), text='测试。', selected=name))
        job = dict(id=ident, voice={}, synthesis={'join_interval': 0.}, segments=segments)
        manifest = read_json(export_job(self.root, job)['artifacts'][1])
        self.assertEqual(manifest['total_samples'], 3200)
        self.assertEqual(manifest['segments'][1]['start_sample'], 1600)

    def test_does_not_guess_between_voices(self):
        for name in ('一号', '二号'):
            ident = new_id()
            write_json(self.root / 'voices' / ident / 'voice.json', dict(id=ident, name=name))
        with self.assertRaises(CastError):
            select_voice(self.root)
        self.assertEqual(select_voice(self.root, '二号')['name'], '二号')

    def test_split_preserves_script_content_and_bounds(self):
        text = '今天介绍声音复制。' * 40 + 'CPU 和 GPU 都是处理器。'
        segments = split_text(text)
        self.assertEqual(''.join(segments), text)
        self.assertTrue(all(len(s) <= 180 for s in segments))
        with self.assertRaises(CastError):
            split_text('   ')

    def test_extraction_rejects_traversal(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as out:
            out.writestr('../escape.txt', 'bad')
        with self.assertRaises(CastError):
            extract(archive, self.root / 'extract')
        self.assertFalse((self.root / 'escape.txt').exists())

    def test_file_ids_cannot_escape_data_root(self):
        with self.assertRaises(CastError):
            item_path(self.root, 'jobs', '../other')

    def test_json_cli_works_from_another_working_directory(self):
        p = subprocess.run([sys.executable, str(RUNTIME / 'cast.py'), '--root', str(self.root), 'voice', 'list'], cwd=self.root, capture_output=True, encoding='utf-8')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['voices'], [])

    def test_feature_dispatch_preserves_unrelated_config(self):
        config = {'features': {'other': {'value': 1}}}
        write_json(self.root / 'config.json', config)
        with patch('castlib.setup.voice_setup', return_value={'status': 'ready'}):
            # Registry is the extension boundary, not hard-coded command branching.
            with patch.dict('castlib.setup.FEATURES', {'new': {'setup': lambda root: {'status': 'ready'}}}):
                self.assertEqual(setup(self.root, 'new')['status'], 'ready')
        self.assertEqual(read_json(self.root / 'config.json'), config)

    def test_hash_verified_download_is_reused_and_mismatch_rejected(self):
        source = self.root / 'source.bin'
        source.write_bytes(b'known resource')
        target = self.root / 'target.bin'
        download(source.as_uri(), target, digest(source), source.stat().st_size)
        stamp = target.stat().st_mtime_ns
        download('https://invalid.example/no-access', target, digest(source), source.stat().st_size)
        self.assertEqual(target.stat().st_mtime_ns, stamp)
        with self.assertRaises(CastError):
            download(source.as_uri(), self.root / 'bad.bin', '0'*64)


if __name__ == '__main__':
    unittest.main()
