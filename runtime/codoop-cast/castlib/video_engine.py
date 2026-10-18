"""Deterministic local HTML -> frames -> H.264/AAC MP4; no HTTP listener."""
import argparse
import base64
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from .contracts import validate,validate_partial,load_records


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def local(directory,name):
    path=(directory/name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(directory) or not path.is_file():
        raise ValueError('Unavailable local scene resource: '+str(name))
    return path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--browser-cache',type=Path,required=True)
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--scene-preview',action='store_true')
    parser.add_argument('--cancel-file',type=Path)
    parser.add_argument('--response',type=Path)
    args=parser.parse_args()
    project=args.package.resolve()
    target=args.output.resolve()
    if target.exists():
        raise ValueError('Use a new output path; existing results are preserved.')
    if args.scene_preview:
        if not args.check_only:
            raise ValueError('Illustrative scene timing cannot be exported as final video.')
        validate_partial(project,'scenes')
    else:
        validated=validate(project)
        if not validated['render_ready']:
            raise ValueError('This project is not render-ready.')
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(args.browser_cache.resolve())
    from playwright.sync_api import sync_playwright
    import imageio_ffmpeg
    records={};record_paths={}
    for entry in read(project/'package.json')['artifacts']:
        artifact=read(local(project,entry['path']))
        records[artifact['kind']]=artifact
        record_paths[artifact['kind']]=entry['path']
    if args.scene_preview:
        planned=records['video-script']['data']['scenes']
        records['timeline']=dict(data=dict(duration_samples=5000*len(planned),sample_rate=1000,
            scenes=[dict(scene_id=s['id'],start_sample=i*5000,end_sample=(i+1)*5000,
                events=[dict(id=e['id'],target_id=e['target_id'],action=e['action'],at_sample=i*5000+min(4000,(n+1)*400)) for n,e in enumerate(s['events'])]) for i,s in enumerate(planned)]))
        records['alignment']=dict(data=dict(units=[],cues=[]))
    profile,tl=records['output-profile']['data'],records['timeline']['data']
    audio=None if args.scene_preview else local(project,records['audio']['data']['media_path'])
    visuals=read(project/'visuals.json') if (project/'visuals.json').exists() else None
    entries={s['id']:local(project,s['entry']) for s in records['scene']['data']['items']}
    fps,width,height=profile['fps'],profile['width'],profile['height']
    if width%2 or height%2:
        raise ValueError('H.264 yuv420p export requires even dimensions.')
    duration=tl['duration_samples']/tl['sample_rate']
    frames=math.ceil(tl['duration_samples']*fps/tl['sample_rate'])
    qa=target.parent/(target.stem+'-qa')
    qa.mkdir(parents=True,exist_ok=False)
    errors=[]
    snapshot_times=sorted({min(duration-.04,s['start_sample']/tl['sample_rate']+max(.8,min(2,(s['end_sample']-s['start_sample'])/tl['sample_rate']*.4))) for s in tl['scenes']})
    report=dict(status='running',width=width,height=height,fps=fps,seconds=duration,frames=frames,
        audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest() if audio else None,playwright=importlib.metadata.version('playwright'),
        illustrative_preview_only=args.scene_preview,
        inputs={name:hashlib.sha256(local(project,path).read_bytes()).hexdigest() for name,path in record_paths.items()},
        supplemental_inputs={'visuals.json':hashlib.sha256((project/'visuals.json').read_bytes()).hexdigest()} if visuals is not None else {},
        scene_sha256={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in set(entries.values())},
        checks=[],errors=errors,network_policy='local files only')
    started=time.monotonic()
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=['--disable-background-networking','--disable-features=MediaRouter'])
        report['browser']=browser.version
        context=browser.new_context(viewport=dict(width=width,height=height),device_scale_factor=1,locale='zh-CN',reduced_motion='reduce',offline=True)
        context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(('file:','data:','blob:')) else route.abort())
        page=context.new_page()
        page.on('pageerror',lambda error:errors.append(str(error)))
        current_entry=None
        def show(seconds):
            nonlocal current_entry
            sample=min(tl['duration_samples']-1,round(seconds*tl['sample_rate']))
            active=next(s for s in tl['scenes'] if s['start_sample']<=sample<s['end_sample'])
            entry=entries[active['scene_id']]
            if entry!=current_entry:
                page.goto(entry.as_uri()+'?render=1',wait_until='load')
                page.wait_for_function('!!window.CodoopCast')
                page.evaluate('async()=>{await window.CodoopCast.ready;await document.fonts.ready;}')
                data=dict(profile=records['output-profile'],timeline=records['timeline'],alignment=records['alignment'],
                    storyboard=records['video-script'],assets=records['assets'],asset_base_url=project.as_uri()+'/',
                    audio_url=Path(os.path.relpath(audio,entry.parent)).as_posix() if audio else None,preview_only=args.scene_preview)
                if visuals is not None:
                    data['visuals']=visuals
                page.evaluate('(data)=>window.CodoopCast.configure(data)',data)
                if args.scene_preview:
                    page.evaluate('()=>{const badge=document.createElement("div");badge.textContent="画面草稿 · 时间仅供预览";badge.style.cssText="position:fixed;top:8px;left:8px;z-index:99999;background:#132a33;color:#fff;font:14px sans-serif;padding:6px 10px;border-radius:4px";document.body.appendChild(badge)}')
                current_entry=entry
            return page.evaluate('(time)=>window.CodoopCast.renderAt(time)',seconds)
        for index,seconds in enumerate(snapshot_times,1):
            state=show(seconds)
            check=page.evaluate('window.CodoopCast.inspect()')
            report['checks'].append(check)
            page.screenshot(path=str(qa/f'{index:02}-{state["scene_id"]}.png'))
        if errors or any(c['issues'] for c in report['checks']):
            report.update(status='failed',elapsed_seconds=time.monotonic()-started)
            write(qa/'render.json',report)
            raise ValueError('Scene or layout checks failed; inspect '+str(qa/'render.json'))
        # Seeking backwards must reconstruct the exact same pixels.
        def visible_state():
            return page.evaluate('window.CodoopCast.snapshot ? JSON.stringify(window.CodoopCast.snapshot()) : JSON.stringify([document.querySelector(".scene.active")?.outerHTML,document.querySelector("#subtitle")?.outerHTML,document.querySelector("#avatar")?.outerHTML,document.querySelector(".header")?.outerHTML,document.querySelector(".footer")?.outerHTML])')
        show(snapshot_times[0]); first=page.screenshot(type='png'); first_state=visible_state()
        show(snapshot_times[-1]); show(snapshot_times[0]); repeat=page.screenshot(type='png'); repeat_state=visible_state()
        exact=hashlib.sha256(first).hexdigest()==hashlib.sha256(repeat).hexdigest()
        report['exact_repeat_pixels']=exact
        report['exact_repeat_dom']=first_state==repeat_state
        report['deterministic_seek']=exact and report['exact_repeat_dom']
        if not exact:
            # Chromium can vary a few antialiasing channel values after a
            # compositing layer is rebuilt. Never accept geometry/clock drift.
            ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
            def pixels(png):
                return subprocess.run([ffmpeg,'-v','error','-i','pipe:0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],
                                      input=png,capture_output=True,check=True).stdout
            a,b=pixels(first),pixels(repeat)
            if len(a)==len(b):
                changes=[abs(x-y) for x,y in zip(a,b) if x!=y]
                report['repeatability_channel_differences']=len(changes)
                report['repeatability_max_channel_delta']=max(changes,default=0)
                report['repeatability_mean_absolute_error']=sum(changes)/len(a)
                report['deterministic_seek']=report['exact_repeat_dom'] and max(changes,default=0)<=3 and sum(changes)/len(a)<=.1
        if not report['deterministic_seek']:
            (qa/'determinism-first.png').write_bytes(first)
            (qa/'determinism-repeat.png').write_bytes(repeat)
            report['status']='failed'
            write(qa/'render.json',report)
            raise ValueError('Scene depends on previous playback state.')
        if not args.check_only:
            temp=target.with_name(target.stem+'.rendering.mp4')
            if temp.exists():
                raise ValueError('An unfinished render already exists: '+str(temp))
            ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
            with (qa/'ffmpeg.log').open('wb') as log:
                proc=subprocess.Popen([ffmpeg,'-hide_banner','-loglevel','error','-n','-f','image2pipe','-vcodec','mjpeg','-framerate',str(fps),'-i','pipe:0',
                    '-i',str(audio),'-map','0:v:0','-map','1:a:0',
                    '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
                    '-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',
                    '-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
                    '-c:a','aac','-b:a','192k','-af','apad','-t',str(duration),'-movflags','+faststart',str(temp)],stdin=subprocess.PIPE,stdout=log,stderr=log)
                cdp=context.new_cdp_session(page)
                try:
                    for frame in range(frames):
                        if args.cancel_file and args.cancel_file.exists():
                            raise KeyboardInterrupt('Video task cancelled')
                        show(frame/fps)
                        shot=cdp.send('Page.captureScreenshot',dict(format='jpeg',quality=90,fromSurface=True))
                        proc.stdin.write(base64.b64decode(shot['data']))
                        if frame%(fps*5)==0:
                            print(json.dumps(dict(frame=frame,total_frames=frames,seconds=round(frame/fps,2)),ensure_ascii=False),flush=True)
                    proc.stdin.close()
                    if proc.wait(timeout=120)!=0:
                        raise ValueError('FFmpeg encoding failed; inspect its log.')
                    if errors:
                        raise ValueError('HTML runtime errors occurred during encoding.')
                except BaseException:
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait(timeout=20)
                    raise
            os.replace(temp,target)
            report['video_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        browser.close()
    report.update(status='checked' if args.check_only else 'rendered',elapsed_seconds=time.monotonic()-started)
    write(qa/'render.json',report)
    response=dict(status='ready',verification=report['status'],output=str(target) if not args.check_only else None,qa=str(qa),
                  preview_only=args.scene_preview,review_required=True)
    if args.response:
        write(args.response,response)
    print(json.dumps(response,ensure_ascii=False))


if __name__=='__main__':
    main()
