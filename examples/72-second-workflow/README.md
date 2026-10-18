# A production-package example for 72-second narration

[English](README.md) | [简体中文](README.zh-cn.md)

This is a structural contract example, not a completed video. Its script comes from the accepted 304-character demonstration, without invented research/evidence. Four paragraphs match old generated chunks for legacy-adapter illustration; formal paragraphs/TTS chunks may map many-to-many.

- script.json: original/spoken text and stable paragraph IDs.
- video-script.json: four scenes, screen text and paragraph anchors; no required images/generation.
- assets.json: empty collection, extensible for actual visual needs.
- scene.json: planned HTML manifest without executable scene entries.
- audio.json: actual rate/sample count/chunk boundaries and script ranges; private audio is not distributed and its path is empty.
- alignment.json: pending real alignment, without words/cues.
- timeline.json: explicitly blocked, not guessed scene times.
- output-profile.json: editable 1080×1920/30fps sample with caption/avatar settings, not an approved user default.
- package.json: relative artifact paths and SHA-256.

Update indexed hashes after changing artifacts. In an isolated environment with jsonschema==4.23.0, run `scripts/validate_production.py examples/72-second-workflow` from the repository root. Passing establishes contract checks, not actual sync, typography, encoding or visual acceptance.
