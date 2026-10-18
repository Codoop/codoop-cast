# Video skills usage

[English](18-video-skills-running.md) | [简体中文](../zh-cn/18-video-skills-running.md)

> Historical implementation record. Current capabilities/gaps: [readiness](29-release-readiness.md); first use: [installation](28-install-and-first-video.md).

On 2026-10-17 the validated HTML prototype became three independent skills with shared setup, superseding the preceding unwrapped-prototype state.

## User entry

| Skill | Independent input | Delivery |
| --- | --- | --- |
| codoop-cast-storyboard | Narration text/script.json | Standard plan, semantic anchors, review and index |
| codoop-cast-scenes | Storyboard package | Topic-specific HTML/manifest/check screenshots |
| codoop-cast-video | Plan, scenes, real audio/alignment | Actual timeline, editable package, MP4 |

Users describe intent; the agent reads skills, authors and calls local tools. Planning/design is agent work, not a fixed ten-page algorithm. Prepare imports text and canonical files; an empty folder is not a generated storyboard. No HTTP service.

## On-demand setup

Registered voice, alignment, authoring and video. Authoring installs jsonschema/dependencies only. Video privately pins Playwright 1.56.0, imageio-ffmpeg 0.6.0 and jsonschema 4.23.0. Official Playwright installs build 1194; verify executable SHA-256, version, offline launch/screenshots and FFmpeg launch. Constraints ship with runtime.

External narration does not require voice models; planning does not require a browser. Private resources share one root, without global Python/PATH/driver edits. Windows is locally validated, AMD/macOS not. CPU H.264 rendering does not inherently require NVIDIA encoding hardware.

## Local commands

Use `scripts/cast.ps1` or compatible Python with `runtime/codoop-cast/cast.py`. Global `--root` precedes the command. The agent operates files/commands, not the user.

```text
storyboard prepare --text-file <narration.txt> --output <new-plan>
# Or retain the imported artifact ID/revision/paragraph IDs:
storyboard prepare --script-file <script.json> --output <new-plan>
project index --package <package>
storyboard validate --package <package>
scenes validate --package <package>
scenes check --package <package> --output <new-preview.mp4>
video compile --package <source> --output <new-production-package>
video check --package <production-package> --output <new-check.mp4>
video render --package <production-package> --output <new-video.mp4>
task status --job <task-id>
task cancel --job <render-task-id>
```

Check writes a matching `-qa` directory/reports/screenshots, not MP4. Scenes without audio use explicitly labeled illustrative timing, never final timing. Video check uses actual timing. Cancel works between export frames; render resume is unavailable. Resolve concrete language for plain-text preparation under the [language policy](25-language-configuration.md).

Use `--accept-reviewed-alignment` only for the exact previously reviewed audio/alignment with existing conservative-group warnings, not to bypass invalid ranges. Changed audio/text needs new validation.

## Packages/changes

Schemas ship with code. After edits, explicitly index hashes; agents maintain revisions/references because index does not fix stale ones. Validation distinguishes storyboard/scene phases and permits missing downstream artifacts.

HTML implements `render-at-time-v1`: configure, ready, renderAt, inspect and snapshot. Reconstruct motion from absolute time, loading local files. Declare auxiliary CSS/JS/images/fonts as assets for compilation. Visuals are topic-specific. Hide trailing caption punctuation, retaining internal punctuation/meaningful symbols.

Output-profile owns aspect, resolution, fps, caption style and avatar position. Implement genuine relayout, not stretching. Default avatar is a placeholder; no lip-sync person. Compile into new directories and retain old projects. Visual edits reuse speech, but final export still renders the whole video; no frame cache.

At this historical stage agent checks reconciled preplanned paragraph IDs/revisions manually, and there was no identity-preserving TTS adapter. Reusing subtitle script.json or explicitly coordinated references was necessary; identical prose alone did not justify timestamp reuse. See [later adapter](22-script-audio-adapter.md).

## Validation record

- Shared setup succeeded and repeat doctor was ready.
- Forty-nine tests passed: 37 ordinary/12 contracts, including no-audio plans, missing real audio, stale refs/hashes, bad anchors and imported identity.
- Six skill format checks passed.
- Complete fallback installation and copied commands worked in isolated Chinese/space directories, not claiming every native host.
- A separate fruit-topic HTML with one scene/different DOM and no audio/alignment passed visual and repeated-seek checks; screenshots viewed.
- The accepted landscape package compiled/rendered through public commands to 72-second 1920×1080/30fps/2160-frame MP4, decoding fully without new speech; retained reports/input hashes/representative frames.

Pending then: research/writing, full workflow/batch, caching/invalidation, preplanned identity adapter, real-avatar media, more native hosts/AMD/macOS and license preparation. Agent content quality still needs review; current completion is tracked in readiness.
