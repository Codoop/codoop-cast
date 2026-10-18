from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/codoop-cast'))
from castlib.common import CastError
from castlib.subtitles import generate,verify_audio_segments


class SubtitleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def wav(self,name,frames):
        path=self.root/name
        with wave.open(str(path),'wb') as stream:
            stream.setparams((1,2,16000,0,'NONE','not compressed'))
            stream.writeframes(frames)
        return str(path)

    def test_selected_audio_must_match_content_not_only_duration(self):
        audio=self.wav('final.wav',b'\x01\x00'*1600)
        chunk=self.wav('chunk.wav',b'\x01\x00'*1600)
        manifest=dict(audio=audio,sample_rate=16000,total_samples=1600,
                      segments=[dict(file=chunk,start_sample=0,end_sample=1600)])
        verify_audio_segments(manifest)
        self.wav('chunk.wav',b'\x02\x00'*1600)
        with self.assertRaisesRegex(CastError,'content differs'):
            verify_audio_segments(manifest)

    def test_existing_output_rejected_before_installation(self):
        with patch('castlib.subtitles.setup') as installer:
            with self.assertRaises(CastError):
                generate(self.root,source_job='unused',output=self.root)
            installer.assert_not_called()

    def test_external_audio_requires_script_before_installation(self):
        audio=self.wav('source.wav',b'\x01\x00'*1600)
        with patch('castlib.subtitles.setup') as installer:
            with self.assertRaisesRegex(CastError,'transcript'):
                generate(self.root,audio=audio)
            installer.assert_not_called()

    def test_source_job_and_unrelated_script_cannot_be_combined(self):
        with self.assertRaisesRegex(CastError,'own selected texts'):
            generate(self.root,source_job='unused',text_file='other.txt')
