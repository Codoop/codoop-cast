# Configured video production

[English](31-production-configuration.md) | [简体中文](../zh-cn/31-production-configuration.md)

Production reads shared/project preferences before choosing visual layout. Users describe defaults or a one-time exception; the agent writes configuration and propagates it through the workflow. Files stay in the shared `config.json` or project/batch `.codoop-cast/config.json`, alongside output_language.

```json
{
  "schema_version": 1,
  "output_language": "zh-CN",
  "video": {
    "orientation": "portrait",
    "resolution": { "width": 1080, "height": 1920 },
    "fps": 30,
    "subtitle_style": {
      "font_family": "Microsoft YaHei",
      "font_size": 48,
      "color": "#FFFFFF",
      "bottom_margin_ratio": 0.12
    },
    "avatar": {
      "enabled": true,
      "mode": "placeholder",
      "x": 0.78, "y": 0.68,
      "width": 0.14, "height": 0.105
    }
  }
}
```

The complete example is at repository root `codoop-cast.config.example.json`. These Windows-oriented font/placeholder defaults do not establish font portability or real-avatar support on all hosts.

## Inheritance and validation

Video settings merge by field: built-in → legacy project defaults → shared defaults → outer-to-nearest scope → task. A project overriding landscape still inherits frame rate/style. Language retains its existing task/nearest/shared/legacy/auto precedence.

Resolution is actual width/height, not a label. Positive even pixels are required for H.264 yuv420p. FPS is a positive integer. Explicit orientation/dimensions must agree. Orientation alone swaps existing dimensions; square uses the shorter side. Returning from square to portrait/landscape needs dimensions. Dimensions alone infer orientation. Invalid bounds, nonfinite coordinates and out-of-canvas avatars fail before preparing outputs.

## Agent commands

The video patch file contains only the fields inside `video`, for example `{"orientation":"landscape","resolution":{"width":1920,"height":1080}}`; it is not a full config or artifact envelope.

```text
setup --directory <scope> --output-language zh-CN --video-config-file <video-patch.json>
config show --directory <project>
config show --directory <project> --video-config-file <one-time-patch.json>
produce plan --directory <project> --video-config-file <one-time-patch.json>
storyboard prepare --script-file <script.json> --video-config-file <one-time-patch.json> --output <new-directory>
```

Only setup saves preferences. Show/plan/prepare overlays do not change defaults. Featureless setup downloads no model. An explicit --profile-file is the task's complete output specification and is mutually exclusive with a prepare patch; preserve its identity. Existing language-only configs continue working.

## Workflow behavior

1. Resolve language and video requirements before planning.
2. Pin effective settings in new visual workflow plans; pass matching settings into prepare.
3. Create output-profile.json and design storyboard, scenes, captions/avatar clearance for it.
4. Compile/render against the package's exact profile, not changing shared defaults during rendering.
5. Register/checkpoint only matching actual profiles when video preferences are explicit.

A changed effective format requires a new visual plan. Reuse report/script/audio/alignment, preserve semantic scene intent, relayout visuals and export a new version. Assets may need a new dependency record but suitable files can be reused without regeneration. Different configured selected visual packages cannot satisfy a new format by silent reuse. Research-only and speech-only runs do not depend on video settings.

Old plans without snapshots remain readable; old packages are preserved rather than rewritten. Complete imported packages pin their own specification. Applying defaults to such a package requires adapting a new mutable copy and updating dependent references before rendering. Existing stage versions remain immutable.

Automated checks cover preference merging, validation, task override persistence, profile creation, plan invalidation and checkpoint mismatch rejection. They do not prove visual quality for every arbitrary resolution/style. This change does not re-synthesize speech or claim new hardware validation.
