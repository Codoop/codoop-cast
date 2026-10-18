"""Video environment entrypoint. Browser control uses local pipes, not a service."""
import argparse
import os
from pathlib import Path
import sys

if '--probe' in sys.argv:
    parser=argparse.ArgumentParser()
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    from castlib.common import read_json,digest
    spec=read_json(Path(__file__).parent/'resources-video.json')
    if digest(args.root/spec['browser_relative_path'])!=spec['browser_sha256']:
        raise RuntimeError('Pinned browser checksum mismatch')
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(args.root/'browsers/video')
    from playwright.sync_api import sync_playwright
    import imageio_ffmpeg
    import subprocess
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        if browser.version!=spec['browser_version']:
            raise RuntimeError('Pinned browser version mismatch')
        page=browser.new_page(viewport=dict(width=64,height=64),offline=True)
        page.set_content('<html><body style="margin:0;background:#123456">local probe</body></html>')
        if len(page.screenshot())<100:
            raise RuntimeError('Browser screenshot probe failed')
        browser.close()
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-version'],stdout=subprocess.DEVNULL,check=True)
    print('Private browser launch, screenshot and FFmpeg probes passed.')
else:
    from castlib.video_engine import main
    main()
