import tempfile,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib import project,produce
from castlib.common import CastError,read_json,write_json,digest

class ProduceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);project.initialize(self.root)
 def tearDown(self):self.tmp.cleanup()
 def stage(self,stage,version='v001',deps=(),select=True,state='ready'):
  folder=self.root/stage/version
  for name in project.STAGES[stage]:
   p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture',encoding='utf-8')
  project.register(self.root,stage,version,deps,state)
  if select:project.select(self.root,stage,version)
 def record(self,result):return read_json(result['plan'])
 def test_old_saved_plan_routes_to_current_skill_names(self):
  result=produce.plan(self.root,target='research')
  plan=read_json(result['plan']);plan['steps'][0]['skill']='codoop-cast-research'
  write_json(result['plan'],plan)
  state=read_json(result['state']);state['plan_sha256']=digest(result['plan']);write_json(result['state'],state)
  restored=produce.status(self.root,result['run_id'])
  self.assertEqual(restored['next_steps'][0]['skill'],'codoop-research')
  self.assertEqual(read_json(result['plan'])['steps'][0]['skill'],'codoop-cast-research')
 def test_new_project_expands_all_prerequisites(self):
  result=produce.plan(self.root)
  self.assertEqual({s['stage'] for s in self.record(result)['steps']},set(produce.GRAPH))
  self.assertEqual([s['stage'] for s in result['next_steps']],['research'])
 def test_imported_script_is_entrypoint_without_research(self):
  self.stage('script');result=produce.plan(self.root,target='voice')
  self.assertEqual([(s['stage'],s['action']) for s in self.record(result)['steps']],[('script','reuse'),('voice','build')])
 def test_forced_voice_keeps_scenes_and_script(self):
  self.stage('script');self.stage('voice',deps=['script=v001']);self.stage('subtitles',deps=['voice=v001']);self.stage('scenes')
  result=produce.plan(self.root,force=['voice']);steps={s['stage']:s['action'] for s in self.record(result)['steps']}
  self.assertEqual(steps['script'],'reuse');self.assertEqual(steps['scenes'],'reuse')
  self.assertEqual(steps['voice'],'build');self.assertEqual(steps['subtitles'],'build')
  self.assertNotIn('research',steps)
 def test_changed_selection_requires_replan(self):
  self.stage('script');result=produce.plan(self.root,target='voice');self.stage('script','v002')
  self.assertEqual(produce.status(self.root,result['run_id'])['workflow_state'],'needs_replan')
  with self.assertRaises(CastError):produce.update(self.root,result['run_id'],'voice','start')
 def test_changed_files_require_replan(self):
  self.stage('script');result=produce.plan(self.root,target='voice');(self.root/'script/v001/script.txt').write_text('changed')
  self.assertEqual(produce.status(self.root,result['run_id'])['workflow_state'],'needs_replan')
 def test_checkpoint_records_and_selects_actual_version(self):
  self.stage('research');r=produce.plan(self.root,target='script');produce.update(self.root,r['run_id'],'script','start')
  self.stage('script',deps=['research=v001'],select=False)
  result=produce.update(self.root,r['run_id'],'script','checkpoint',version='v001',job_id='actual-task')
  self.assertEqual(result['workflow_state'],'complete');self.assertEqual(project.locate(self.root)[1]['current']['script'],'v001')
 def test_wrong_dependencies_rejected(self):
  self.stage('research');r=produce.plan(self.root,target='script');produce.update(self.root,r['run_id'],'script','start')
  self.stage('script',select=False)
  with self.assertRaisesRegex(CastError,'dependencies differ'):produce.update(self.root,r['run_id'],'script','checkpoint',version='v001')
 def test_start_requires_upstream_completion(self):
  r=produce.plan(self.root)
  with self.assertRaisesRegex(CastError,'upstream'):produce.update(self.root,r['run_id'],'voice','start')
 def test_failure_and_targeted_retry_preserve_history(self):
  self.stage('script');r=produce.plan(self.root,target='voice');run=r['run_id']
  produce.update(self.root,run,'voice','start');produce.update(self.root,run,'voice','fail',message='model error',job_id='task-one')
  self.assertEqual(produce.status(self.root,run)['workflow_state'],'failed')
  result=produce.update(self.root,run,'voice','start')
  self.assertEqual(result['steps']['voice']['attempts'],2)
  state=read_json(result['state']);self.assertTrue(any(e['job_id']=='task-one' for e in state['events']))
 def test_running_stage_cannot_restart_silently(self):
  self.stage('script');r=produce.plan(self.root,target='voice');produce.update(self.root,r['run_id'],'voice','start')
  with self.assertRaisesRegex(CastError,'already started'):produce.update(self.root,r['run_id'],'voice','start')
 def test_partial_is_review_not_completed(self):
  self.stage('research',state='partial');r=produce.plan(self.root,target='research')
  self.assertEqual(r['next_steps'][0]['action'],'review');self.assertNotEqual(r['workflow_state'],'complete')
 def test_plan_edit_detected(self):
  self.stage('script');r=produce.plan(self.root,target='voice');p=Path(r['plan']);p.write_text(p.read_text()+' ')
  self.assertEqual(produce.status(self.root,r['run_id'])['workflow_state'],'needs_replan')
 def test_ready_target_is_reused_without_new_work(self):
  self.stage('script');r=produce.plan(self.root,target='script')
  self.assertEqual(r['workflow_state'],'complete');self.assertEqual(len(r['steps']),1)
 def test_unverified_export_is_not_reused_as_complete(self):
  self.stage('exports');r=produce.plan(self.root)
  self.assertNotEqual(r['workflow_state'],'complete')
  self.assertEqual(next(s for s in self.record(r)['steps'] if s['stage']=='exports')['action'],'review')
 def test_forced_rebuild_cannot_checkpoint_old_selection(self):
  self.stage('script');self.stage('voice',deps=['script=v001']);r=produce.plan(self.root,target='voice',force=['voice'])
  produce.update(self.root,r['run_id'],'voice','start')
  with self.assertRaisesRegex(CastError,'new version'):produce.update(self.root,r['run_id'],'voice','checkpoint',version='v001')
 def test_failure_is_recorded_even_when_inputs_changed_midtask(self):
  self.stage('script');r=produce.plan(self.root,target='voice');produce.update(self.root,r['run_id'],'voice','start')
  self.stage('script','v002')
  result=produce.update(self.root,r['run_id'],'voice','fail',message='input changed while working')
  self.assertEqual(result['workflow_state'],'needs_replan')
  self.assertEqual(read_json(result['state'])['steps']['voice']['message'],'input changed while working')
 def test_unrelated_forced_stage_rejected(self):
  with self.assertRaises(CastError):produce.plan(self.root,target='research',force=['voice'])

if __name__=='__main__':unittest.main()
