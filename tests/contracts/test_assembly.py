import json,shutil,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib import project,produce
from castlib.common import digest,read_json,write_json
from castlib.contracts import index_artifacts
from castlib.assembly import assemble

class AssemblyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);project.initialize(self.root)
  self.scene=self.root/'scenes/v001';shutil.copytree(ROOT/'examples/72-second-workflow',self.scene)
  manifest=read_json(self.scene/'scene.json')
  for item in manifest['data']['items']:item.update(status='ready',entry='scenes/index.html')
  write_json(self.scene/'scene.json',manifest)
  self.sub=self.root/'subtitles/v001';self.sub.mkdir(parents=True)
  for name in ('script.json','audio.json','alignment.json'):shutil.copyfile(self.scene/name,self.sub/name)
  audio=read_json(self.sub/'audio.json');audio['data'].update(media_available=True,media_path='media/narration.wav');write_json(self.sub/'audio.json',audio)
  (self.sub/'media').mkdir()
  with wave.open(str(self.sub/'media/narration.wav'),'wb') as f:
   f.setparams((1,2,audio['data']['sample_rate'],0,'NONE','not compressed'));f.writeframes(b'\x01\x00'*audio['data']['total_samples'])
  (self.sub/'subtitles.srt').write_text('fixture',encoding='utf-8')
 def tearDown(self):self.tmp.cleanup()
 def run_plan(self):
  index_artifacts(self.scene)
  for stage in ('scenes','subtitles'):
   project.register(self.root,stage,'v001');project.select(self.root,stage,'v001')
  r=produce.plan(self.root);produce.update(self.root,r['run_id'],'exports','start')
  return r['run_id']
 def test_assembly_preserves_pinned_inputs_and_copies_media(self):
  run=self.run_plan();before=digest(self.scene/'script.json');result=assemble(self.root,run)
  out=Path(result['package']);self.assertFalse(result['render_ready'])
  self.assertEqual(digest(out/'script.json'),before)
  self.assertEqual(digest(out/'media/narration.wav'),digest(self.sub/'media/narration.wav'))
  project.checked_record(self.root,'scenes','v001');project.checked_record(self.root,'subtitles','v001')
 def test_different_script_provenance_is_not_silently_reconciled(self):
  script=read_json(self.sub/'script.json');script['data']['provenance']='different';write_json(self.sub/'script.json',script)
  run=self.run_plan()
  with self.assertRaisesRegex(ValueError,'different script artifacts'):assemble(self.root,run)
 def test_resource_collision_rejected(self):
  (self.scene/'media').mkdir();asset=self.scene/'media/narration.wav';asset.write_bytes(b'conflicting image')
  assets=read_json(self.scene/'assets.json');assets['data']['items']=[dict(id='collision',path='media/narration.wav',sha256=digest(asset),origin='fixture',usage_notes='test')];write_json(self.scene/'assets.json',assets)
  run=self.run_plan()
  with self.assertRaisesRegex(ValueError,'Conflicting assembly'):assemble(self.root,run)
 def test_audio_sample_mismatch_rejected(self):
  with wave.open(str(self.sub/'media/narration.wav'),'wb') as f:
   f.setparams((1,2,32000,0,'NONE','not compressed'));f.writeframes(b'\x01\x00'*100)
  run=self.run_plan()
  with self.assertRaisesRegex(ValueError,'Audio samples differ'):assemble(self.root,run)

if __name__=='__main__':unittest.main()
