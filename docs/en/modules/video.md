# Video production module

[English](video.md) | [简体中文](../../zh-cn/modules/video.md)

Historical progress: standard-script → HTML → MP4 prototype, [sample](../17-html-video-validation.md), before public skills/shared setup. Later status is in [video usage](../18-video-skills-running.md).

## I/O

Inputs: script, audio, captions/alignment, assets, style, aspect, fps, avatar settings. Outputs: storyboard, unified timeline, preview, MP4 and rendering manifest. Existing scripts/audio/captions are independent inputs.

## Two phases

Planning chooses visual types, semantic/keyword anchors, information hierarchy and material needs. Timing reads actual audio/alignment for scenes, events and captions. Accepted paragraph boundaries can substitute for missing word times without pretending word precision.

## Optional visual approaches

| Approach | Content/motion |
| --- | --- |
| Question opening | Brief question, slow background move |
| Concept explanation | Simple diagram/progressive keywords |
| Media explanation | Image/video, annotations, subtle camera movement |
| Comparison | Side-by-side items highlighted with narration |
| Conclusion | One-sentence takeaway/clean finish |

These are options, not a fixed shot list. The agent authors HTML/CSS/SVG against seeking, readiness, inspection and resource contracts. Local frame rendering uses one clock, not real-time screen capture. Topic content/animation is not hardcoded in the framework.

Emphasize one main idea per visual, avoiding full narration on screen or a scene switch per cue.

## Avatar, captions and assets

- Independent lower-right avatar track starts with static/placeholder animation; real video is a later extension.
- Keep avatar/captions/content clear of one another; configure platform safe areas.
- Prefer owned material, retaining external origin/use terms.
- Missing media can use relevant cards/diagrams, not unrelated filler.
- Check fonts/media availability/rights before rendering, which should read prepared local files.

## Rendering/checks

Provide a cheaper preview, then profile-based final export. Before rendering check assets, cue bounds, total clock and fields. Afterward verify streams/aspect/duration/playability and view opening/ending/transitions/long cues.

Suggested acceptance: ~one-minute sample with several approaches, lower-right avatar and Chinese mixed text. Check clear audio/readable captions/unobstructed content and replace one asset while reusing speech/alignment.

Complete final re-rendering is acceptable initially; add scene/incremental caching only for measured bottlenecks.
