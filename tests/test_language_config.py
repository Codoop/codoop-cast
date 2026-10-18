import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'))
from castlib import config, project, produce, batch
from castlib.common import CastError, read_json, write_json
from castlib.locale import labels, ZH


class LanguageConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.shared = self.root / 'private'
        self.env = patch.dict(os.environ, CODOOP_CAST_HOME=str(self.shared))
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_precedence_and_unknown_settings_survive_setup(self):
        config.configure(output_language='en-US', data_root=self.shared)
        write_json(self.shared/'config.json', dict(schema_version=1, output_language='en-US', features={'voice': {'keep': True}}))
        config.configure(data_root=self.shared)
        self.assertTrue(read_json(self.shared/'config.json')['features']['voice']['keep'])
        collection = self.root/'collection'
        config.configure(collection, 'zh-cn')
        child = collection/'projects/topic'
        project.initialize(child)
        self.assertEqual(config.resolve(child)['output_language'], 'zh-CN')
        config.configure(child, 'en')
        self.assertEqual(config.resolve(child/'script/v001')['output_language'], 'en')
        self.assertEqual(config.resolve(child, 'ja')['output_language'], 'ja')
        self.assertEqual(config.resolve(child)['output_language'], 'en')
        self.assertFalse((self.shared/'envs').exists())

    def test_unconfigured_and_legacy_project(self):
        self.assertEqual(config.resolve(self.root)['output_language'], 'auto')
        folder = self.root/'old'
        project.initialize(folder)
        data = read_json(folder/project.MARKER)
        data['defaults']['language'] = 'zh'
        write_json(folder/project.MARKER, data)
        self.assertEqual(config.resolve(folder)['output_language'], 'zh')
        config.configure(output_language='en', data_root=self.shared)
        self.assertEqual(config.resolve(folder)['output_language'], 'en')

    def test_invalid_language_and_unsupported_backend_fail_clearly(self):
        for value in ('../en', '', None, 'en US'):
            with self.assertRaises(CastError):
                config.language_tag(value)
        self.assertEqual(config.speech_language('en-US'), 'en')
        self.assertEqual(config.speech_language('zh-CN'), 'zh')
        for value in ('auto', 'ja'):
            with self.assertRaises(CastError):
                config.speech_language(value)

    def test_mismatch_does_not_relabel_content(self):
        artifact = dict(data=dict(language='zh', paragraphs=[dict(display_text='unchanged')]))
        config.configure(self.root, 'en')
        with self.assertRaisesRegex(CastError, 'translated revision'):
            config.check_artifact_language(artifact, self.root)
        self.assertEqual(artifact['data']['language'], 'zh')
        self.assertEqual(config.check_artifact_language(artifact, self.root, 'zh-CN'), 'zh')

    def test_language_change_requires_replan(self):
        folder = self.root/'project'
        project.initialize(folder)
        config.configure(folder, 'en')
        run = produce.plan(folder, target='research')
        self.assertEqual(run['output_language'], 'en')
        config.configure(folder, 'zh-CN')
        self.assertEqual(produce.status(folder, run['run_id'])['workflow_state'], 'needs_replan')
        overridden = produce.plan(folder, target='research', language='en')
        config.configure(folder, 'ja')
        self.assertEqual(produce.status(folder, overridden['run_id'])['workflow_state'], 'pending')

    def test_existing_different_language_is_rebuilt(self):
        folder = self.root/'project'
        project.initialize(folder)
        out = folder/'research/v001'
        write_json(out/'report.json', dict(data=dict(language='zh')))
        (out/'report.md').write_text('previous version', encoding='utf-8')
        project.register(folder, 'research', 'v001')
        project.select(folder, 'research', 'v001')
        config.configure(folder, 'en')
        run = produce.plan(folder, target='research')
        plan = read_json(run['plan'])
        self.assertEqual(plan['steps'][0]['action'], 'build')
        self.assertEqual((out/'report.md').read_text(encoding='utf-8'), 'previous version')

    def test_custom_locale_required_and_complete(self):
        with self.assertRaises(CastError):
            labels('ja', self.root)
        write_json(self.root/'.codoop-cast/locales/ja.json', {'Scope': 'scope'})
        with self.assertRaises(CastError):
            labels('ja', self.root)
        write_json(self.root/'.codoop-cast/locales/ja.json', {key: 'translation '+key for key in ZH})
        self.assertEqual(labels('ja', self.root)('Scope'), 'translation Scope')

    def test_batch_report_uses_collection_language(self):
        folder = self.root/'batch'
        batch.create(folder)
        config.configure(folder, 'en')
        report = batch.report(folder)
        text = Path(report['report']).read_text(encoding='utf-8')
        self.assertIn('# Batch production report', text)
        self.assertIn('| Project | Status | Artifact | Notes |', text)

    def test_speech_records_target_separately_from_reference_language(self):
        from castlib import voice
        write_json(self.shared/'features/voice.json', dict(model={'test': True}))
        reference = dict(language='zh', id='reference')
        with patch.object(voice, 'select_voice', return_value=reference), patch.object(voice, 'ensure'), patch.object(voice, 'run_job', return_value={'status':'ready'}):
            voice.generate(self.shared, text='An English sentence.', language='en-US')
        jobs = list((self.shared/'jobs').glob('*/job.json'))
        saved = read_json(jobs[0])
        self.assertEqual(saved['language'], 'en-US')
        self.assertEqual(saved['text_language'], 'en')
        self.assertEqual(saved['voice']['language'], 'zh')
        with patch.object(voice, 'ensure') as install:
            with self.assertRaises(CastError):
                voice.generate(self.shared, text='Unsupported language.', language='ja')
            install.assert_not_called()


if __name__ == '__main__':
    unittest.main()
