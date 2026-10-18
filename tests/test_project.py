import json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib import project
from castlib.common import CastError

class ProjectTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'content';project.initialize(self.root,'测试项目')
 def tearDown(self):self.tmp.cleanup()
 def stage(self,stage,version='v001',deps=(),state='ready'):
  folder=self.root/stage/version
  for name in project.STAGES[stage]:
   p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('content',encoding='utf-8')
  project.register(self.root,stage,version,deps,state);project.select(self.root,stage,version)
  return folder
 def test_init_preserves_existing_files_and_is_idempotent(self):
  p=self.root/'notes.txt';p.write_text('keep')
  result=project.initialize(self.root,'replace')
  self.assertFalse(result['created']);self.assertEqual(project.inspect_project(self.root)['name'],'测试项目')
  self.assertEqual(p.read_text(),'keep');self.assertFalse((self.root/'voice').exists())
 def test_discover_parent_project(self):
  child=self.root/'work';child.mkdir()
  self.assertEqual(project.locate(child)[0],self.root)
 def test_next_path_is_not_created_or_selected(self):
  result=project.next_path(self.root,'research')
  self.assertEqual(result['version'],'v001');self.assertFalse(Path(result['output']).exists())
  (self.root/'research/v003').mkdir(parents=True)
  self.assertEqual(project.next_path(self.root,'research')['version'],'v004')
 def test_registration_does_not_select_latest(self):
  self.stage('research');self.stage('research','v002');project.select(self.root,'research','v001')
  self.assertEqual(project.inspect_project(self.root)['stages']['research']['version'],'v001')
 def test_dependency_change_marks_transitive_outputs_stale(self):
  self.stage('research');self.stage('script',deps=['research=v001']);self.stage('storyboard',deps=['script=v001'])
  self.stage('research','v002')
  status=project.inspect_project(self.root)['stages']
  self.assertEqual(status['research']['state'],'ready');self.assertEqual(status['script']['state'],'stale')
  self.assertEqual(status['storyboard']['state'],'stale')
 def test_registered_content_change_is_invalid(self):
  folder=self.stage('research');(folder/'report.md').write_text('changed')
  self.assertEqual(project.inspect_project(self.root)['stages']['research']['state'],'invalid')
 def test_unrecorded_file_is_invalid(self):
  folder=self.stage('research');(folder/'extra.txt').write_text('new')
  self.assertEqual(project.inspect_project(self.root)['stages']['research']['state'],'invalid')
 def test_missing_required_files_cannot_register(self):
  (self.root/'research/v001').mkdir(parents=True)
  with self.assertRaises(CastError):project.register(self.root,'research','v001')
 def test_nested_project_rejected(self):
  with self.assertRaises(CastError):project.initialize(self.root/'nested')
 def test_traversal_and_noncanonical_versions_rejected(self):
  for v in ('../outside','v000','v0001','v1'):
   with self.assertRaises(CastError):project.select(self.root,'research',v)
 def test_registered_version_cannot_be_overwritten(self):
  self.stage('research')
  with self.assertRaises(CastError):project.register(self.root,'research','v001')
 def test_partial_state_preserved(self):
  self.stage('research',state='partial')
  self.assertEqual(project.inspect_project(self.root)['stages']['research']['state'],'partial')
 def test_moving_whole_project_preserves_dependencies(self):
  self.stage('research');self.stage('script',deps=['research=v001'])
  moved=self.root.parent/'moved';shutil.move(str(self.root),str(moved));self.root=moved
  self.assertEqual(project.inspect_project(moved)['stages']['script']['state'],'ready')

if __name__=='__main__':unittest.main()
