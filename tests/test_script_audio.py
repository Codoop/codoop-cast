import copy,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib.common import CastError,new_id,item_path,read_json,write_json
from castlib.script_audio import prepare_script,paragraph_mapping,compose_mapping,fingerprint,verify_script_job,remap_display_units
from castlib.textmap import normalization_map,project_spans
from castlib.voice import narration_text,export_job,run_job
from unittest.mock import patch

def artifact(text,spoken=None):
 return dict(schema_version='0.1.0',kind='script',artifact_id='source-script',revision=7,data=dict(language='zh',provenance='fixture',paragraphs=[dict(id='original-paragraph',display_text=text,spoken_text=spoken or text,claim_ids=['original-claim'])]))

def job_for(script):
 chunks=prepare_script(script)
 return dict(script_artifact=script,script_fingerprint=fingerprint(script),segments=[dict(chunk,text=narration_text(chunk['spoken_text'])) for chunk in chunks])

class ScriptAudioTests(unittest.TestCase):
 def test_long_paragraph_keeps_full_unicode_ranges(self):
  source=artifact('这是长段落。'*45+'最终结束。');chunks=prepare_script(source)
  self.assertGreater(len(chunks),1)
  self.assertEqual(''.join(c['spoken_text'] for c in chunks),source['data']['paragraphs'][0]['spoken_text'])
  self.assertEqual(''.join(c['display_text'] for c in chunks),source['data']['paragraphs'][0]['display_text'])
  self.assertEqual({c['display_span']['paragraph_id'] for c in chunks},{'original-paragraph'})
 def test_number_override_preserves_display_and_spoken(self):
  source=artifact('今天有3个人。','今天有三个人。');chunk=prepare_script(source)[0]
  actual=normalization_map(chunk['spoken_text'],'今天有三个人。')
  mapping=compose_mapping(chunk['requested_mapping'],actual)
  self.assertEqual(project_spans(mapping,[(3,4)]),[(3,4)])
  self.assertEqual(mapping['display_text'],'今天有3个人。')
 def test_explicit_pronunciation_composes_with_frontend(self):
  source=artifact('重庆有3位访客。','崇庆有三位访客。');p=source['data']['paragraphs'][0]
  p['pronunciation_spans']=[dict(display_start=0,display_end=2,spoken_start=0,spoken_end=2)]
  chunk=prepare_script(source)[0]
  actual=compose_mapping(chunk['requested_mapping'],normalization_map(chunk['spoken_text'],chunk['spoken_text']))
  self.assertEqual(project_spans(actual,[(0,1)]),[(0,2)])
 def test_ambiguous_rewrite_not_guessed(self):
  with self.assertRaises(CastError):prepare_script(artifact('原来的含义。','完全不同的意思。'))
 def test_out_of_bounds_pronunciation_rejected(self):
  source=artifact('重庆。','崇庆。');source['data']['paragraphs'][0]['pronunciation_spans']=[dict(display_start=0,display_end=99,spoken_start=0,spoken_end=2)]
  with self.assertRaises(CastError):prepare_script(source)
 def test_atomic_override_not_cut_between_chunks(self):
  source=artifact('甲'*98+'重庆'+'乙'*10,'甲'*98+'崇庆'+'乙'*10)
  source['data']['paragraphs'][0]['pronunciation_spans']=[dict(display_start=98,display_end=100,spoken_start=98,spoken_end=100)]
  chunks=prepare_script(source,limit=99)
  self.assertEqual(chunks[0]['script_spans'][0]['end'],100)
 def test_remap_chunk_units_to_original_offsets(self):
  chunks=prepare_script(artifact('甲'*205))
  units=[dict(id='u',script_span=dict(paragraph_id='p002',start=1,end=2),start_sample=5,end_sample=6)]
  mapped=remap_display_units(units,chunks)
  self.assertEqual(mapped[0]['script_span'],dict(paragraph_id='original-paragraph',start=101,end=102))
  self.assertEqual(units[0]['script_span']['paragraph_id'],'p002')
 def test_changed_script_or_chunk_rejected(self):
  job=job_for(artifact('测试原稿。'));verify_script_job(job)
  job['segments'][0]['text']='改成其他内容。'
  with self.assertRaises(CastError):verify_script_job(job)
  job=job_for(artifact('测试原稿。'));job['script_artifact']['revision']=8
  with self.assertRaises(CastError):verify_script_job(job)
 def test_duplicate_paragraph_ids_rejected(self):
  source=artifact('测试。');source['data']['paragraphs']*=2
  with self.assertRaises(CastError):prepare_script(source)
 def test_long_trailing_punctuation_stays_with_readable_chunk(self):
  source=artifact('甲'*99+'。'*5)
  self.assertEqual(len(prepare_script(source)),1)
 def test_structured_retry_rejects_text_replacement(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);job=job_for(artifact('保持原稿。'));ident=new_id();job.update(id=ident)
   write_json(item_path(root,'jobs',ident)/'job.json',job)
   with patch('castlib.voice.ensure'):
    with self.assertRaisesRegex(CastError,'script revision'):
     run_job(root,ident,retry=1,replacement='替换的内容。')
   self.assertEqual(read_json(item_path(root,'jobs',ident)/'job.json')['segments'][0]['text'],'保持原稿。')
 def test_structured_export_copies_manifest_and_original_script(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);script=artifact('测试3。');job=job_for(script);ident=new_id();directory=item_path(root,'jobs',ident);directory.mkdir(parents=True)
   job.update(id=ident,voice=dict(id='fixture'),original_text='测试3。',narration_text='测试3。',synthesis=dict(join_interval=0))
   for n,s in enumerate(job['segments']):
    name=f'{n}.wav'
    with wave.open(str(directory/name),'wb') as out:
     out.setparams((1,2,16000,0,'NONE','not compressed'));out.writeframes(b'\x01\x00'*1000)
    s.update(id=new_id(),selected=name,attempts=[dict(file=name,normalized_text='测试三。',text_mapping=normalization_map('测试3。','测试三。'))])
   for name in ('original.txt','narration.txt'):(directory/name).write_text('测试3。',encoding='utf-8')
   output=root/'voice/v001/narration.wav';result=export_job(root,job,output)
   self.assertEqual(read_json(output.parent/'script.json'),script)
   manifest=read_json(output.with_suffix('.json'))
   self.assertEqual(manifest['segments'][0]['script_spans'][0]['paragraph_id'],'original-paragraph')
   self.assertEqual(manifest['audio'],str(output))
   with self.assertRaises(CastError):export_job(root,job,output)

if __name__=='__main__':unittest.main()
