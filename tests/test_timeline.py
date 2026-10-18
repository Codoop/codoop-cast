import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/codoop-cast'))
from castlib.common import CastError
from castlib.timeline import compile_timeline,resolve_anchor


def ref(kind):
    return dict(artifact_id=kind,revision=1)


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.script=dict(**ref('script'),data=dict(paragraphs=[dict(id='p1',display_text='甲乙',spoken_text='甲乙'),dict(id='p2',display_text='丙丁',spoken_text='丙丁')]))
        def anchor(pid,edge):
            return dict(paragraph_id=pid,edge=edge,offset_ms=0)
        plans=[dict(id=f's{i}',paragraph_ids=[f'p{i}'],start_anchor=anchor(f'p{i}','start'),end_anchor=anchor(f'p{i}','end'),events=[]) for i in (1,2)]
        plans[0]['events']=[dict(id='e',target_id='title',action='reveal',anchor=dict(paragraph_id='p1',edge='start',offset_ms=0,text_range=dict(start=1,end=2)))]
        self.storyboard=dict(**ref('storyboard'),data={'script':ref('script'),'output-profile':ref('profile'),'scenes':plans})
        self.audio=dict(**ref('audio'),data=dict(script=ref('script'),sample_rate=1000,total_samples=1000))
        units=[dict(id=str(i),script_span=dict(paragraph_id=pid,start=pos,end=pos+1),start_sample=start,end_sample=end) for i,(pid,pos,start,end) in enumerate([('p1',0,100,300),('p1',1,400,500),('p2',0,600,800),('p2',1,800,900)])]
        self.alignment=dict(**ref('alignment'),data=dict(script=ref('script'),audio=ref('audio'),state='ready',units=units))
        self.scene=dict(**ref('scene'),data={'video-script':ref('storyboard'),'items':[dict(id=f's{i}',status='ready',element_ids=['title']) for i in (1,2)]})
        self.profile=dict(**ref('profile'))

    def compile(self,**kwargs):
        return compile_timeline(self.script,self.storyboard,self.audio,self.alignment,self.scene,self.profile,**kwargs)['data']

    def test_real_samples_cover_initial_silence_and_inter_scene_pauses(self):
        timeline=self.compile()
        self.assertEqual([(s['start_sample'],s['end_sample']) for s in timeline['scenes']],[(0,600),(600,1000)])
        self.assertEqual(timeline['scenes'][0]['content_end_sample'],500)
        self.assertEqual(timeline['scenes'][0]['events'][0]['at_sample'],400)

    def test_stale_artifact_revision_is_rejected(self):
        self.storyboard['data']['script']['revision']=2
        with self.assertRaisesRegex(CastError,'revision'):
            self.compile()

    def test_unreviewed_alignment_cannot_be_silently_accepted(self):
        self.alignment['data']['state']='needs_review'
        with self.assertRaises(CastError):
            self.compile()
        self.assertTrue(self.compile(accept_reviewed_alignment=True)['alignment_review_accepted'])

    def test_invalid_alignment_still_rejected_after_review(self):
        self.alignment['data']['units'][0]['end_sample']=0
        with self.assertRaisesRegex(CastError,'invalid sample ranges'):
            self.compile(accept_reviewed_alignment=True)

    def test_missing_word_anchor_is_not_replaced_with_estimated_time(self):
        anchor=dict(paragraph_id='p1',edge='start',offset_ms=0,text_range=dict(start=2,end=3))
        with self.assertRaises(CastError):
            resolve_anchor(anchor,self.script,self.alignment,1000)

    def test_animation_cannot_escape_its_scene(self):
        self.storyboard['data']['scenes'][0]['events'][0]['anchor']['offset_ms']=700
        with self.assertRaisesRegex(CastError,'outside its scene'):
            self.compile()
