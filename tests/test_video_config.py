import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'runtime/codoop-cast'))
from castlib import config, project, produce
from castlib.common import CastError, digest, read_json, write_json
from castlib.video_config import DEFAULT, apply, profile_data, resolve_video


class VideoConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.private = self.root/'private'
        self.env = patch.dict(os.environ, CODOOP_CAST_HOME=str(self.private))
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_per_field_inheritance_and_task_override(self):
        config.configure(output_language='en', data_root=self.private, video=dict(fps=60, subtitle_style=dict(font_size=40)))
        collection = self.root/'batch'
        config.configure(collection, video=dict(orientation='landscape'))
        folder = collection/'projects/topic'
        project.initialize(folder)
        config.configure(folder, video=dict(avatar=dict(enabled=False)))
        result = resolve_video(folder/'scenes/v001', dict(resolution=dict(width=1280, height=720)))['video']
        self.assertEqual(result['orientation'], 'landscape')
        self.assertEqual(result['resolution'], dict(width=1280, height=720))
        self.assertEqual(result['fps'], 60)
        self.assertEqual(result['subtitle_style']['font_size'], 40)
        self.assertFalse(result['avatar']['enabled'])
        self.assertEqual(config.resolve(folder)['output_language'], 'en')
        self.assertEqual(read_json(folder/project.MARKER)['defaults']['output'], dict(width=1920, height=1080, fps=60))

    def test_orientation_only_swaps_actual_dimensions(self):
        result = apply(DEFAULT, dict(orientation='landscape'))
        self.assertEqual(result['resolution'], dict(width=1920, height=1080))
        self.assertEqual(apply(DEFAULT, dict(resolution=dict(width=720, height=1280)))['orientation'], 'portrait')
        self.assertEqual(apply(DEFAULT, dict(orientation='square'))['resolution'], dict(width=1080, height=1080))

    def test_invalid_preferences_fail(self):
        for value in (dict(orientation='landscape', resolution=dict(width=1080, height=1920)),
                      dict(resolution=dict(width=721, height=1280)), dict(resolution=dict(width=720)),
                      dict(fps=True), dict(fps=0), dict(avatar=dict(x=.99)), dict(subtitle_style=dict(bottom_margin_ratio=float('nan'))),
                      dict(unrecognized=1), dict(avatar=dict(unrecognized=1))):
            with self.subTest(value=value), self.assertRaises(CastError):
                apply(DEFAULT, value)

    def test_setup_preserves_other_preferences_and_normalizes_changes(self):
        config.configure(output_language='zh-CN', data_root=self.private, video=dict(resolution=dict(width=1080, height=1920), fps=60))
        data = read_json(self.private/'config.json')
        data['features'] = {'voice': {'preserve': True}}
        write_json(self.private/'config.json', data)
        config.configure(data_root=self.private, video=dict(orientation='landscape'))
        result = read_json(self.private/'config.json')
        self.assertEqual(result['video']['resolution'], dict(width=1920, height=1080))
        self.assertEqual(result['video']['fps'], 60)
        self.assertTrue(result['features']['voice']['preserve'])
        self.assertEqual(result['output_language'], 'zh-CN')

    def test_invalid_update_does_not_save_partial_configuration(self):
        config.configure(self.root, 'en', self.private, dict(fps=30))
        file = self.root/config.RELATIVE
        before = file.read_bytes()
        with self.assertRaises(CastError):
            config.configure(self.root, 'zh-CN', self.private, dict(fps=-1))
        self.assertEqual(before, file.read_bytes())

    def test_global_setup_does_not_inherit_cwd_project_overrides(self):
        folder = self.root/'project'
        config.configure(folder, video=dict(avatar=dict(width=.05)))
        original = Path.cwd()
        try:
            os.chdir(folder)
            with self.assertRaises(CastError):
                config.configure(data_root=self.private, video=dict(avatar=dict(x=.9)))
            result = config.configure(data_root=self.private, video=dict(fps=60))
            self.assertEqual(result['video']['avatar']['width'], .14)
        finally:
            os.chdir(original)

    def stage(self, folder, stage, dependencies=(), profile=None):
        output = folder/stage/'v001'
        for name in project.STAGES[stage]:
            path = output/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture', encoding='utf-8')
        if profile:
            write_json(output/'output-profile.json', dict(data=profile))
        project.register(folder, stage, 'v001', dependencies)
        project.select(folder, stage, 'v001')

    def test_format_change_rebuilds_visual_branch_and_reuses_audio(self):
        folder = self.root/'project'
        project.initialize(folder)
        for stage, dependencies in [('script', []), ('storyboard', ['script=v001']), ('assets', ['storyboard=v001']),
                                    ('scenes', ['storyboard=v001','assets=v001']), ('voice', ['script=v001']), ('subtitles', ['voice=v001'])]:
            self.stage(folder, stage, dependencies, profile_data(DEFAULT) if stage in ('storyboard','scenes') else None)
        old_audio = digest(folder/'voice/v001/narration.wav')
        config.configure(folder, video=dict(orientation='landscape'))
        result = produce.plan(folder)
        steps = {s['stage']:s['action'] for s in read_json(result['plan'])['steps']}
        self.assertEqual(steps['script'], 'reuse')
        self.assertEqual(steps['subtitles'], 'reuse')
        self.assertNotIn('voice', steps)
        self.assertEqual(steps['storyboard'], 'build')
        self.assertEqual(steps['scenes'], 'build')
        self.assertEqual(old_audio, digest(folder/'voice/v001/narration.wav'))
        self.assertEqual(result['video']['resolution'], dict(width=1920, height=1080))

    def test_video_change_requires_replan_only_for_visual_runs(self):
        folder = self.root/'project'
        project.initialize(folder)
        config.configure(folder, video=dict(orientation='portrait'))
        visual = produce.plan(folder, target='storyboard')
        research = produce.plan(folder, target='research')
        explicit = produce.plan(folder, target='storyboard', video=dict(orientation='landscape'))
        config.configure(folder, video=dict(orientation='landscape'))
        self.assertEqual(produce.status(folder, visual['run_id'])['workflow_state'], 'needs_replan')
        self.assertEqual(produce.status(folder, research['run_id'])['workflow_state'], 'pending')
        self.assertEqual(produce.status(folder, explicit['run_id'])['workflow_state'], 'pending')

    def test_checkpoint_rejects_profile_different_from_pinned_spec(self):
        folder = self.root/'project'
        project.initialize(folder)
        self.stage(folder, 'script')
        config.configure(folder, video=dict(orientation='landscape'))
        run = produce.plan(folder, target='storyboard')
        produce.update(folder, run['run_id'], 'storyboard', 'start')
        self.stage(folder, 'storyboard', ['script=v001'], profile_data(DEFAULT))
        with self.assertRaisesRegex(CastError, 'Output profile differs'):
            produce.update(folder, run['run_id'], 'storyboard', 'checkpoint', version='v001')

    def test_old_plan_without_video_snapshot_remains_readable(self):
        folder = self.root/'project'
        project.initialize(folder)
        result = produce.plan(folder, target='storyboard')
        plan = read_json(result['plan'])
        for key in ('video', 'video_override', 'video_enforced'):
            plan.pop(key)
        write_json(result['plan'], plan)
        state = read_json(result['state'])
        state['plan_sha256'] = digest(result['plan'])
        write_json(result['state'], state)
        config.configure(folder, video=dict(orientation='landscape'))
        self.assertEqual(produce.status(folder, result['run_id'])['workflow_state'], 'pending')

    def test_cli_setup_and_task_preview(self):
        folder = self.root/'project'
        patch_file = self.root/'video.json'
        write_json(patch_file, dict(orientation='landscape', resolution=dict(width=1280, height=720), fps=60))
        cli = [sys.executable, str(ROOT/'runtime/codoop-cast/cast.py'), '--root', str(self.private)]
        saved = subprocess.run([*cli,'setup','--directory',str(folder),'--output-language','en','--video-config-file',str(patch_file)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(saved.returncode, 0, saved.stdout+saved.stderr)
        self.assertEqual(json.loads(saved.stdout)['video']['fps'], 60)
        write_json(patch_file, dict(orientation='portrait'))
        preview = subprocess.run([*cli,'config','show','--directory',str(folder),'--video-config-file',str(patch_file)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(preview.returncode, 0, preview.stdout+preview.stderr)
        self.assertEqual(json.loads(preview.stdout)['video']['resolution'], dict(width=720, height=1280))
        self.assertEqual(resolve_video(folder)['video']['orientation'], 'landscape')
        write_json(patch_file, None)
        rejected = subprocess.run([*cli,'setup','--directory',str(folder),'--video-config-file',str(patch_file)], capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(rejected.returncode, 0)
