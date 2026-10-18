"""Compile semantic anchors to actual audio samples, without duration guesses."""
from .common import CastError


def reference(artifact):
    return {k:artifact[k] for k in ('artifact_id','revision')}


def require_ref(value,artifact):
    if value != reference(artifact):
        raise CastError('stale_reference','An input references a different artifact revision.')


def resolve_anchor(anchor,script,alignment,rate):
    paragraphs={p['id']:p for p in script['data']['paragraphs']}
    pid=anchor['paragraph_id']
    if pid not in paragraphs or anchor['edge'] not in ('start','end'):
        raise CastError('invalid_anchor','Unknown paragraph or anchor edge.')
    basis=alignment['data'].get('span_basis','spoken_text')
    length=len(paragraphs[pid][basis])
    span=anchor.get('text_range',dict(start=0,end=length))
    if not 0<=span['start']<span['end']<=length:
        raise CastError('invalid_anchor','Anchor text range is outside its paragraph.')
    units=[u for u in alignment['data']['units'] if u['script_span']['paragraph_id']==pid and
           u['script_span']['start']<span['end'] and u['script_span']['end']>span['start']]
    if not units:
        raise CastError('unresolved_anchor','No actual audio alignment covers the anchor.')
    sample=(units[0]['start_sample'] if anchor['edge']=='start' else units[-1]['end_sample'])+round(anchor.get('offset_ms',0)*rate/1000)
    return sample


def compile_timeline(script,storyboard,audio,alignment,scene,profile,accept_reviewed_alignment=False):
    for value,artifact in [(storyboard['data']['script'],script),(audio['data']['script'],script),
        (alignment['data']['script'],script),(alignment['data']['audio'],audio),
        (scene['data']['video-script'],storyboard),(storyboard['data']['output-profile'],profile)]:
        require_ref(value,artifact)
    if alignment['data']['state']!='ready' and not accept_reviewed_alignment:
        raise CastError('alignment_review_required','Review the alignment before compiling a final video.')
    if any(s['status']!='ready' for s in scene['data']['items']):
        raise CastError('scenes_not_ready','Build the HTML scenes before compiling the final timeline.')
    rate,total=audio['data']['sample_rate'],audio['data']['total_samples']
    previous=0
    for unit in alignment['data']['units']:
        if not previous<=unit['start_sample']<unit['end_sample']<=total:
            raise CastError('invalid_alignment','Alignment has invalid sample ranges.')
        previous=unit['end_sample']
    planned=storyboard['data']['scenes']
    if not planned:
        raise CastError('empty_storyboard','At least one scene is required.')
    scene_items={s['id']:s for s in scene['data']['items']}
    if set(scene_items)!={s['id'] for s in planned} or len(scene_items)!=len(planned):
        raise CastError('scene_mismatch','Scene IDs must match the storyboard exactly.')
    starts=[resolve_anchor(s['start_anchor'],script,alignment,rate) for s in planned]
    if any(a>=b for a,b in zip(starts,starts[1:])) or starts[0]<0 or starts[-1]>=total:
        raise CastError('invalid_scene_order','Scene anchor times must increase within the audio.')
    # Hold the opening over initial silence, and each scene over the following
    # pause. Scene content still retains its separately resolved end anchor.
    starts[0]=0
    resolved=[]
    for index,plan in enumerate(planned):
        start=starts[index]
        end=starts[index+1] if index+1<len(starts) else total
        content_end=resolve_anchor(plan['end_anchor'],script,alignment,rate)
        if not start<content_end<=end:
            raise CastError('overlapping_scene_content','A scene content end exceeds its next scene boundary.')
        events=[]
        for event in plan['events']:
            if event['target_id'] not in scene_items[plan['id']]['element_ids']:
                raise CastError('missing_animation_target','An animation targets an unknown scene element.')
            at=resolve_anchor(event['anchor'],script,alignment,rate)
            if not start<=at<end:
                raise CastError('event_outside_scene','An animation anchor is outside its scene.')
            events.append(dict(id=event['id'],target_id=event['target_id'],action=event['action'],at_sample=at))
        resolved.append(dict(scene_id=plan['id'],start_sample=start,end_sample=end,content_end_sample=content_end,events=events))
    return dict(schema_version='0.1.0',kind='timeline',artifact_id=storyboard['artifact_id']+'-timeline',revision=1,
        data={'video-script':reference(storyboard),'audio':reference(audio),'alignment':reference(alignment),
              'scene':reference(scene),'output-profile':reference(profile),'state':'ready','duration_samples':total,
              'sample_rate':rate,'alignment_review_accepted':bool(accept_reviewed_alignment),'scenes':resolved,'blockers':[]})


def storyboard_review(script,storyboard,timeline,directory=None):
    from .locale import labels
    t = labels(script['data'].get('language', 'zh'), directory)
    paragraphs={p['id']:p['display_text'] for p in script['data']['paragraphs']}
    blocks=['# ' + t('Video storyboard review'),t('Narration is preserved; the following links content to actual audio timing.')]
    rate=timeline['data']['sample_rate']
    for index,(scene,timed) in enumerate(zip(storyboard['data']['scenes'],timeline['data']['scenes']),1):
        parts=[]
        for pid in scene['paragraph_ids']:
            text=paragraphs[pid]
            start=scene['start_anchor'].get('text_range',dict(start=0))['start'] if pid==scene['start_anchor']['paragraph_id'] else 0
            end=scene['end_anchor'].get('text_range',dict(end=len(text)))['end'] if pid==scene['end_anchor']['paragraph_id'] else len(text)
            parts.append(text[start:end])
        events=[]
        for event,resolved in zip(scene['events'],timed['events']):
            anchor=event['anchor'];span=anchor.get('text_range',dict(start=0,end=len(paragraphs[anchor['paragraph_id']])))
            quote=paragraphs[anchor['paragraph_id']][span['start']:span['end']]
            events.append('- ' + t('{seconds} s: {target}, anchored to "{quote}"').format(seconds=f'{resolved["at_sample"]/rate:.2f}', target=event['target_id'], quote=quote))
        blocks.append(f'## {index:02} {scene["intent"]}\n\n{t("Time")}: {timed["start_sample"]/rate:.2f}–{timed["end_sample"]/rate:.2f} s\n\n{t("Narration")}: '+''.join(parts)+'\n\n'+t('Screen')+': '+'; '.join(scene['screen_text'])+'\n\n'+t('Animation anchors')+':\n\n'+'\n'.join(events))
    return '\n\n'.join(blocks)+'\n'
