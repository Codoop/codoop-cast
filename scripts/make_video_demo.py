"""Build this topic's authored example from an approved 72-second handoff.

The renderer is generic; these editorial choices belong only to this example.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib.common import read_json,write_json
from castlib.timeline import compile_timeline,reference,storyboard_review


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--orientation',choices=['portrait','landscape'],default='portrait')
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new output directory.')
    script=read_json(args.source/'script.json')
    audio=read_json(args.source/'audio.json')
    alignment=read_json(args.source/'alignment.json')
    paragraphs=script['data']['paragraphs']
    if len(paragraphs)!=4 or audio['data']['total_samples']/audio['data']['sample_rate']!=72:
        raise ValueError('This authored example requires the approved four-block, 72-second script.')
    def anchor(quote,edge='start',offset=0):
        hits=[]
        for p in paragraphs:
            cursor=0
            while (position:=p['display_text'].find(quote,cursor))>=0:
                hits.append((p,position))
                cursor=position+1
        if len(hits)!=1:
            raise ValueError('Expected unique text anchor: '+quote)
        p,start=hits[0]
        return dict(paragraph_id=p['id'],edge=edge,offset_ms=offset,text_range=dict(start=start,end=start+len(quote)))
    def event(key,quote,offset=0):
        return dict(id='event-'+key,target_id=key,action='reveal',anchor=anchor(quote,offset=offset))
    specs=[
        ('intro','大家好','短视频','从一个问题<br>到一条<em>知识视频</em>','让内容一步步成为画面',
         [event('report','大家好',350),event('script','大家好',1200),event('video','大家好',2100)]),
        ('question','第一步','什么','先确定<br>一个<em>问题</em>','从观众的收获开始',
         [event('question','观众看完之后'),event('answer','第一步',200)]),
        ('focus','不要','足够了','一个视频<br>讲清楚<em>一件事</em>','信息更少，表达更清楚',
         [event('idea0','不要'),event('idea1','不要',200),event('idea2','不要',400),event('idea3','不要',600),event('one','围绕一个主题')]),
        ('research','第二步','来源','结论之前<br>先找到<em>来源</em>','资料让表达有依据',
         [event('paper0','第二步',100),event('paper1','第二步',500),event('paper2','可靠的来源')]),
        ('explain','再把专业术语','理解','把专业术语<br>翻译成<em>人话</em>','复杂的概念，也可以简单解释',
         [event('before','专业术语'),event('after','日常生活中的表达'),event('example','简单的例子')]),
        ('structure','第三步','建议','口播稿<br>需要<em>清楚的结构</em>','让观众知道为什么、怎么做',
         [event('opening','开头'),event('reason','中间'),event('action','最后')]),
        ('voice','程序','训练模型','让稿件<br>变成<em>你的声音</em>','参考声音与口播稿，生成新的配音',
         [event('reference','程序',100),event('copy','程序',450),event('audio','程序',900),event('automatic','手动裁切')]),
        ('review','生成音频之后','停顿','生成之后<br>再<em>听一遍</em>','音频质量，需要逐项检查',
         [event('check0','漏字'),event('check1','读错'),event('check2','不自然的停顿')]),
        ('sync','确认声音','同一条时间轴上','声音、字幕、画面<br>共用<em>一条时间轴</em>','让每一次出现，都跟上讲解',
         [event('track0','声音'),event('track1','字幕'),event('track2','画面'),event('together','同一条时间轴')]),
        ('finish','这样','内容本身','把时间<br>留给<em>内容本身</em>','少一点重复操作，多一点清楚表达',
         [event('file','这样',150),event('benefit','这样',650)])]
    portrait=args.orientation=='portrait'
    profile=dict(schema_version='0.1.0',kind='output-profile',artifact_id='knowledge-profile',revision=1 if portrait else 2,
        data=dict(width=1080 if portrait else 1920,height=1920 if portrait else 1080,fps=30,
            subtitle_style=dict(font_family='Microsoft YaHei',font_size=48 if portrait else 44,color='#FFFFFF',bottom_margin_ratio=.12 if portrait else .10),
            avatar=dict(enabled=True,mode='placeholder',x=.78 if portrait else .86,y=.68 if portrait else .59,
                        width=.14 if portrait else .075,height=.105 if portrait else .19)))
    assets=dict(schema_version='0.1.0',kind='assets',artifact_id='knowledge-assets',revision=1,data=dict(items=[]))
    storyboard=dict(schema_version='0.1.0',kind='video-script',artifact_id='knowledge-storyboard',revision=1 if portrait else 2,
        data={'script':reference(script),'assets':reference(assets),'output-profile':reference(profile),'scenes':[]})
    visuals,items=[],[]
    for index,(kind,start,end,title,lead,events) in enumerate(specs,1):
        sid=f'scene{index:03}'
        first,last=anchor(start),anchor(end,'end')
        pids=[p['id'] for p in paragraphs]
        related=pids[pids.index(first['paragraph_id']):pids.index(last['paragraph_id'])+1]
        chapter=['从话题到视频','确定问题','聚焦表达','整理资料','通俗解释','口播结构','生成配音','检查声音','音画同步','成片导出'][index-1]
        storyboard['data']['scenes'].append(dict(id=sid,paragraph_ids=related,intent=chapter,
            screen_text=[title.replace('<br>','').replace('<em>','').replace('</em>',''),lead],asset_ids=[],
            start_anchor=first,end_anchor=last,events=events))
        items.append(dict(id=sid,status='ready',entry='scenes/index.html',element_ids=[e['target_id'] for e in events],asset_ids=[],layout_modes=['portrait','landscape']))
        visuals.append(dict(id=sid,type=kind,kicker=f'{index:02} / '+chapter,title=title,lead=lead,chapter=chapter))
    scene=dict(schema_version='0.1.0',kind='scene',artifact_id='knowledge-scenes',revision=1 if portrait else 2,
        data={'video-script':reference(storyboard),'renderer_contract':'render-at-time-v1','items':items})
    timeline=compile_timeline(script,storyboard,audio,alignment,scene,profile,accept_reviewed_alignment=True)
    records=dict(script=script,audio=audio,alignment=alignment,assets=assets,scene=scene,timeline=timeline,
                 **{'video-script':storyboard,'output-profile':profile})
    args.output.mkdir(parents=True,exist_ok=False)
    for name in ('checks.json','subtitles.srt'):
        shutil.copyfile(args.source/name,args.output/name)
    shutil.copytree(args.source/'media',args.output/'media')
    for kind,value in records.items():
        write_json(args.output/(kind+'.json'),value)
    bundle=dict(profile=profile,timeline=timeline,alignment=alignment,visuals=visuals,audio_url='../'+audio['data']['media_path'])
    content=(ROOT/'examples/72-second-workflow/scenes/index.html').read_text(encoding='utf-8')
    embedded='<script>window.CodoopCast.configure('+json.dumps(bundle,ensure_ascii=False).replace('<','\\u003c')+');</script>'
    # JSON escaping protects script boundaries; restore ordinary Unicode escapes.
    embedded=embedded.replace('\\\\u003c','\\u003c')
    (args.output/'scenes').mkdir()
    (args.output/'scenes/index.html').write_text(content.replace('<!-- CAST_BUNDLE -->',embedded),encoding='utf-8')
    write_json(args.output/'visuals.json',visuals)
    write_json(args.output/'review.json',dict(alignment_accepted=True,
        basis='User approved the 72-second Chinese audio and subtitle synchronization in this session.',
        audio_sha256=read_json(args.source/'checks.json')['audio_sha256']))
    write_json(args.output/'package.json',dict(schema_version='0.1.0',artifacts=[dict(path=k+'.json',sha256=hashlib.sha256((args.output/(k+'.json')).read_bytes()).hexdigest()) for k in records]))
    (args.output/'storyboard.md').write_text(storyboard_review(script,storyboard,timeline),encoding='utf-8')
    print(json.dumps(dict(status='ready',project=str(args.output.resolve()),scenes=len(specs),seconds=72),ensure_ascii=False))


if __name__=='__main__':
    main()
