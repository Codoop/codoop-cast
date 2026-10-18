import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'runtime/codoop-cast'))
from authoring_worker import prepare
from castlib import config
from castlib.common import read_json, write_json


class VideoPreferenceContractTests(unittest.TestCase):
    def test_prepare_reads_config_and_exports_valid_profile(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, CODOOP_CAST_HOME=str(Path(temp)/'private')):
            folder = Path(temp)/'project'
            config.configure(folder, video=dict(orientation='landscape', resolution=dict(width=1280, height=720), fps=60,
                                               subtitle_style=dict(font_size=36), avatar=dict(enabled=False)))
            output = folder/'storyboard/v001'
            prepare(dict(script_file=str(ROOT/'examples/script-subtitle-timing/script.json'), output=str(output)))
            profile = read_json(output/'output-profile.json')
            Draft202012Validator(read_json(ROOT/'schemas/output-profile.schema.json')).validate(profile)
            self.assertEqual((profile['data']['width'], profile['data']['height'], profile['data']['fps']), (1280,720,60))
            self.assertEqual(profile['data']['subtitle_style']['font_size'], 36)
            self.assertFalse(profile['data']['avatar']['enabled'])

    def test_explicit_profile_and_task_patch_override_defaults_without_saving(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, CODOOP_CAST_HOME=str(Path(temp)/'private')):
            folder = Path(temp)/'project'
            config.configure(folder, video=dict(orientation='landscape'))
            source = ROOT/'examples/script-subtitle-timing/script.json'
            explicit = ROOT/'examples/72-second-workflow/output-profile.json'
            prepare(dict(script_file=str(source), profile_file=str(explicit), output=str(folder/'explicit')))
            self.assertEqual(read_json(folder/'explicit/output-profile.json'), read_json(explicit))
            prepare(dict(script_file=str(source), video_config=dict(orientation='portrait'), output=str(folder/'task')))
            self.assertEqual(read_json(folder/'task/output-profile.json')['data']['width'], 1080)
            self.assertEqual(read_json(folder/config.RELATIVE)['video']['orientation'], 'landscape')

    def test_config_example_matches_schema(self):
        Draft202012Validator(read_json(ROOT/'schemas/config.schema.json')).validate(read_json(ROOT/'codoop-cast.config.example.json'))
