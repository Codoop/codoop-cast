import json,sys,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib import batch,project,produce
from castlib.common import CastError,read_json,write_json

class BatchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.queue=self.root/'collection';batch.create(self.queue)
 def tearDown(self):self.tmp.cleanup()
 def content(self,name,ready=False):
  p=self.root/name;project.initialize(p)
  if ready:
   for file in project.STAGES['script']:
    path=p/'script/v001'/file;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture',encoding='utf-8')
   project.register(p,'script','v001');project.select(p,'script','v001')
  return p
 def add(self,name,ready=False,target='script'):
  return batch.add(self.queue,self.content(name,ready),target=target)
 def test_add_topic_creates_named_project_in_managed_folder(self):
  result=batch.add(self.queue,topic='测试话题',target='research')
  path=Path(result['project']);self.assertTrue(path.is_relative_to(self.queue/'projects'))
  self.assertEqual(project.locate(path)[1]['name'],'测试话题')
 def test_complete_projects_are_reused_without_work(self):
  self.add('one',True);self.add('two',True)
  result=batch.next_item(self.queue)
  self.assertEqual(result['batch_state'],'complete');self.assertEqual(result['counts']['succeeded'],2)
  self.assertIsNone(result['active_item'])
 def test_claim_is_idempotent_and_sequential(self):
  first=self.add('one',target='research');self.add('two',target='research')
  a=batch.next_item(self.queue);b=batch.next_item(self.queue)
  self.assertEqual(a['active_item']['id'],first['item_id']);self.assertEqual(a['active_item']['run_id'],b['active_item']['run_id'])
  self.assertEqual(b['counts']['active'],1);self.assertEqual(b['counts']['pending'],1)
 def test_deferred_item_does_not_block_later_project(self):
  first=self.add('one',target='research');self.add('two',True)
  batch.next_item(self.queue);batch.control(self.queue,'defer',first['item_id'],'missing material',True)
  result=batch.next_item(self.queue)
  self.assertEqual(result['counts']['needs_input'],1);self.assertEqual(result['counts']['succeeded'],1)
  self.assertEqual(result['batch_state'],'needs_attention')
 def test_removed_pending_project_is_recorded_and_next_is_processed(self):
  self.add('one',True);self.add('two',True);shutil.rmtree(self.root/'one')
  result=batch.next_item(self.queue)
  self.assertEqual(result['counts']['failed'],1);self.assertEqual(result['counts']['succeeded'],1)
 def test_duplicate_project_rejected(self):
  first=self.add('one',True)
  with self.assertRaisesRegex(CastError,'already queued'):batch.add(self.queue,first['project'])
 def test_copied_project_identity_not_queued_twice(self):
  self.add('one',True);shutil.copytree(self.root/'one',self.root/'copy')
  with self.assertRaises(CastError):batch.add(self.queue,self.root/'copy')
 def test_pause_does_not_start_pending_item(self):
  self.add('one',target='research');batch.control(self.queue,'pause')
  self.assertIsNone(batch.next_item(self.queue)['active_item'])
  batch.control(self.queue,'resume');self.assertIsNotNone(batch.next_item(self.queue)['active_item'])
 def test_cancel_does_not_restart_entries_on_resume(self):
  first=self.add('one',True);batch.control(self.queue,'cancel');batch.control(self.queue,'resume')
  self.assertEqual(batch.next_item(self.queue)['counts']['cancelled'],1)
  batch.control(self.queue,'retry',first['item_id']);self.assertEqual(batch.next_item(self.queue)['counts']['succeeded'],1)
 def test_cancel_keeps_active_worker_visible(self):
  self.add('one',target='research');r=batch.next_item(self.queue);batch.control(self.queue,'cancel')
  after=batch.next_item(self.queue)
  self.assertTrue(after['cancel_requested']);self.assertEqual(after['active_item']['run_id'],r['active_item']['run_id'])
 def test_retry_reuses_run_and_history(self):
  first=self.add('one',target='research');a=batch.next_item(self.queue);run=a['active_item']['run_id']
  batch.control(self.queue,'defer',first['item_id'],'temporary error');batch.control(self.queue,'retry',first['item_id'])
  result=batch.next_item(self.queue);item=result['active_item']
  self.assertEqual(item['run_id'],run);self.assertEqual(item['attempts'],2);self.assertEqual(len(item['run_history']),1)
 def test_running_workflow_cannot_be_silently_deferred(self):
  first=self.add('one',target='research');a=batch.next_item(self.queue)
  produce.update(first['project'],a['active_item']['run_id'],'research','start')
  with self.assertRaisesRegex(CastError,'running workflow'):batch.control(self.queue,'defer',first['item_id'],'skip')
 def test_failed_workflow_releases_slot_after_reconciliation(self):
  first=self.add('one',target='research');self.add('two',True);a=batch.next_item(self.queue);run=a['active_item']['run_id']
  produce.update(first['project'],run,'research','start');produce.update(first['project'],run,'research','fail',message='source unavailable')
  result=batch.next_item(self.queue)
  self.assertEqual(result['counts']['failed'],1);self.assertEqual(result['counts']['succeeded'],1)
 def test_completed_project_change_is_not_silently_rebuilt(self):
  first=self.add('one',True);batch.next_item(self.queue)
  (Path(first['project'])/'script/v001/script.txt').write_text('changed',encoding='utf-8')
  result=batch.status(self.queue)
  self.assertEqual(result['counts']['needs_replan'],1);self.assertEqual(result['counts']['pending'],0)
 def test_project_identity_change_rejected_at_claim(self):
  first=self.add('one',True);p=Path(first['project'])/'cast-project.json';record=read_json(p);record['project_id']='another';write_json(p,record)
  self.assertEqual(batch.next_item(self.queue)['counts']['failed'],1)
 def test_queue_creation_does_not_overwrite_or_nest_in_project(self):
  with self.assertRaises(CastError):batch.create(self.queue)
  p=self.content('one')
  with self.assertRaises(CastError):batch.create(p/'nested-queue')
 def test_other_volume_can_be_explicitly_referenced(self):
  p=self.content('one',True)
  with patch('castlib.batch.os.path.relpath',side_effect=ValueError('different drive')):batch.add(self.queue,p,target='script')
  self.assertEqual(batch.next_item(self.queue)['counts']['succeeded'],1)
 def test_unavailable_active_project_requires_explicit_worker_reconciliation(self):
  first=self.add('one',target='research');self.add('two',True);batch.next_item(self.queue);shutil.rmtree(self.root/'one')
  with self.assertRaisesRegex(CastError,'Worker state is unavailable'):batch.control(self.queue,'defer',first['item_id'],'project removed')
  batch.control(self.queue,'defer',first['item_id'],'verified no live task',worker_stopped=True)
  result=batch.next_item(self.queue)
  self.assertEqual(result['counts']['succeeded'],1)
  self.assertTrue(result['items'][0]['worker_stopped_asserted'])
 def test_reports_preserve_history_and_show_unresolved_items(self):
  first=self.add('one',target='research');self.add('two',True);batch.next_item(self.queue)
  batch.control(self.queue,'defer',first['item_id'],'missing | material',True);batch.next_item(self.queue)
  a=batch.report(self.queue);before=Path(a['report']).read_text(encoding='utf-8');b=batch.report(self.queue)
  self.assertNotEqual(a['report'],b['report']);self.assertEqual(Path(a['report']).read_text(encoding='utf-8'),before)
  self.assertIn('需补充信息',before);self.assertIn('script.md',before);self.assertIn('missing \\| material',before)
 def test_report_does_not_overwrite_user_file(self):
  target=self.root/'report.md';target.write_text('keep',encoding='utf-8')
  with self.assertRaises(CastError):batch.report(self.queue,target)
  self.assertEqual(target.read_text(encoding='utf-8'),'keep')
 def test_batch_and_per_item_briefs_survive_reopening(self):
  shared=self.root/'shared.txt';shared.write_text('横屏，使用已选择的声音。',encoding='utf-8')
  specific=self.root/'specific.txt';specific.write_text('这个话题只做一分钟。',encoding='utf-8')
  queue=self.root/'with-brief';batch.create(queue,brief_file=shared)
  batch.add(queue,topic='测试话题',target='research',brief_file=specific)
  shared.unlink();specific.unlink();result=batch.next_item(queue)
  self.assertEqual(result['brief'],'横屏，使用已选择的声音。')
  self.assertEqual(result['active_item']['brief'],'这个话题只做一分钟。')
 def test_unrelated_force_rejected_before_project_creation(self):
  with self.assertRaises(CastError):batch.add(self.queue,topic='test',target='research',force=['voice'])
  self.assertFalse((self.queue/'projects').exists())

if __name__=='__main__':unittest.main()
