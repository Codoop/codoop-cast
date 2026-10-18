# First HTML animation video sample

[English](17-html-video-validation.md) | [简体中文](../zh-cn/17-html-video-validation.md)

> Historical prototype record. Current status: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

On 2026-10-17 the maintainer combined accepted 72-second speech/captions with standard storyboards, real timing and HTML into MP4. Storyboard/scenes/video skills and generic video setup were not yet packaged at that stage; do not confuse the prototype with installable capabilities.

## Storyboard/handoff

Ten topic-specific units: topic-to-video, defining the question, focusing the explanation, organizing evidence, accessible explanation, narration structure, synthesis, speech checks, audiovisual sync and completion. Their HTML visuals are authored for this topic, not a fixed ten-template requirement.

The package has script, video-script, assets, scene, audio, alignment, timeline and output-profile, plus relative HTML/audio/SRT. Script/audio/alignment came from subtitle task `bb1c99acd09849278d872171ba605042`, with audio SHA-256 matching the accepted version. `review.json` records acceptance of this exact speech/sync in the session, not automatic approval for new inputs.

Word anchors add paragraph ID plus Unicode-codepoint `[start,end)` `text_range` to disambiguate repetition. Compile real alignment sample positions, not guessed seconds. Zero-duration grouping still has group-level precision, not independently measured character timing.

Separate content end from playback end: cover initial silence, hold a scene until the next starts and cover the entire audio tail. Events stay inside scenes. Script edits preserve unchanged visual content and re-resolve affected anchors/offsets; automatic one-command targeted editing was only a design at this point.

## HTML prototype contract

`examples/72-second-workflow/scenes/index.html` exposes `window.CodoopCast`:

- `configure(bundle)`: profile, timeline, alignment and topic visuals.
- `ready`: fonts/resources loaded.
- `renderAt(seconds)`: reconstruct a time directly, independent of playback history.
- `inspect()`: layout/runtime diagnostics.

Animations derive from absolute time, not free-running CSS/randomness. Interactive preview follows audio currentTime. Export disables player loading/timeupdate listeners, with FFmpeg adding audio, avoiding player events resetting frames.

Portrait stacks vertically; landscape uses side-by-side layout rather than stretching. Captions follow profile size/position, balanced wrapping and no trailing punctuation. A lower-right abstract avatar is a placeholder, not real video/lip sync.

## Local rendering

Private `envs/video`: Python 3.10.11, Playwright 1.56.0, imageio-ffmpeg 0.6.0, jsonschema 4.23.0; Chromium Headless Shell 141.0.7390.37/build 1194 in `browsers/video`. Pins: `constraints-video-experiment-windows.txt`. This prototype was manually prepared, not yet generic video setup.

`scripts/make_video_demo.py` edits this topic, not universal storyboarding. `scripts/render_video.py` validates references, actual timing and ready scenes, opens local HTML by file URI and seeks/screenshots each frame. Browser external requests are disabled without HTTP; this is not a system firewall guarantee.

Pipe frames in memory to FFmpeg without thousands of temporary images. Encode H.264/AAC, 30fps, faststart and BT.709 limited-range yuv420p rather than inheriting full-range browser JPEG metadata. Narration remains 32k mono; platform audio presets were pending.

Both aspects run 72 seconds/2160 frames at 1080×1920 and 1920×1080. Inspect a representative frame per scene for bounds/avatar overlap; check full decode, durations, color/streams after export.

Deliveries: `codoop-cast-portrait-final.mp4` (3,572,504 bytes), `codoop-cast-landscape-v3.mp4` (3,315,849 bytes). Both decoded fully with the stated encoding/time/range. Editable packages were combined into `codoop-cast-video-projects.zip`. Encoded-frame review corrected an unwanted landscape title wrap and added an inspect check.

Repeated seeking compares visible DOM and images. Chromium layer rebuilding may cause minor anti-aliasing variation: per-channel maximum difference ≤3, image mean absolute difference ≤0.1, identical visible DOM. Retain raw metrics. This is neither timeline verification nor byte-identical output across browsers/machines.

## Validation/limits

Forty-three tests passed: 37 ordinary/six contracts, including stale versions, unaccepted alignment, illegal times, word anchors, out-of-scene events and silence coverage. Both packages passed eight schemas/cross-file checks.

All graphics are local HTML/CSS/SVG; no generated/external images. Microsoft YaHei is used locally, not redistributed. Font reproducibility/distributable alternatives remain unresolved. Audio is synthesized narration, without personal references/models in the package.

The user must judge communication, pacing and style. Pending at this stage: general storyboarding/scenes skills, video setup, scene/frame caching, complex tracks, real avatars and platform presets. The proposed next step was user feedback, then independent packaging.

Primary references: [Playwright browsers](https://playwright.dev/python/docs/browsers), [screenshots](https://playwright.dev/python/docs/api/class-page#page-screenshot), [FFmpeg scale/range](https://ffmpeg.org/ffmpeg-filters.html#scale).

Subsequent 2026-10-17 update: independent skills/setup/local commands were implemented and tested; see [video skills](18-video-skills-running.md).
