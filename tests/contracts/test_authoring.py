import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib.contracts import index_artifacts,validate_partial,load_records
from authoring_worker import prepare,compile_project

class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.package=self.root/'plan'
        shutil.copytree(ROOT/'examples/72-second-workflow',self.package)
        for kind in ('audio','alignment','timeline','scene'):
            (self.package/(kind+'.json')).unlink()
        index_artifacts(self.package)
    def tearDown(self):
        self.tmp.cleanup()
    def edit(self,kind,fn):
        p=self.package/(kind+'.json');a=json.loads(p.read_text(encoding='utf-8'));fn(a)
        p.write_text(json.dumps(a,ensure_ascii=False),encoding='utf-8');index_artifacts(self.package)
    def test_plan_independent_of_audio_and_scenes(self):
        result=validate_partial(self.package)
        self.assertEqual(result['next_required'],['audio','alignment'])
        self.assertFalse(result['render_ready'])
    def test_stale_script_revision_rejected(self):
        self.edit('video-script',lambda a:a['data']['script'].update(revision=9))
        with self.assertRaisesRegex(ValueError,'Stale script'):
            validate_partial(self.package)
    def test_unindexed_content_change_rejected(self):
        p=self.package/'script.json';p.write_text(p.read_text(encoding='utf-8')+' ',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            load_records(self.package)
    def test_display_anchor_range_rejected(self):
        self.edit('video-script',lambda a:a['data']['scenes'][0]['start_anchor'].update(text_range=dict(start=0,end=99999)))
        with self.assertRaisesRegex(ValueError,'display text'):
            validate_partial(self.package)
    def test_compile_requires_actual_audio(self):
        shutil.copyfile(ROOT/'examples/72-second-workflow/scene.json',self.package/'scene.json')
        self.edit('scene',lambda a:[item.update(status='ready',entry='scenes/index.html') for item in a['data']['items']])
        with self.assertRaisesRegex(ValueError,'actual audio'):
            compile_project(dict(package=str(self.package),output=str(self.root/'compiled')))
    def test_prepare_preserves_imported_script_identity(self):
        out=self.root/'prepared';source=self.package/'script.json'
        result=prepare(dict(script_file=str(source),output=str(out)))
        self.assertFalse(result['storyboard_created'])
        self.assertEqual(json.loads(source.read_text(encoding='utf-8')),load_records(out)['script'])
        with self.assertRaisesRegex(ValueError,'new authoring'):
            prepare(dict(script_file=str(source),output=str(out)))

if __name__=='__main__':unittest.main()
