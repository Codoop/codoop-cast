# Installation and first video

[English](28-install-and-first-video.md) | [简体中文](../zh-cn/28-install-and-first-video.md)

Alpha status: local Windows/NVIDIA Chinese speech, alignment and MP4 are tested. Complete-copy fallback installation has isolated tests. Native Codex/Claude Code/Cursor installation still needs host-by-host acceptance; manifest presence is insufficient.

## Ask the agent to install

Provide the repository/complete source and ask:

> Install codoop-cast, retaining skills, runtime, scripts and schemas. Check that my agent discovers the skills. Do not download voice models yet.

Do not copy only SKILL.md; it needs bundled runtime. The plugin itself needs no HTTP service/API key. Research/image generation use available host tools, whose availability must be checked.

Maintainers can use the fallback from the source root with an existing compatible Python 3.10+. The installer does not bootstrap Python itself:

```powershell
python scripts/install_skills.py --agent codex --dry-run
python scripts/install_skills.py --agent codex
```

Use --agent claude or cursor for those targets. Defaults are user .codex/.claude/.cursor; explicit custom locations use --agent-home, not guessed configuration paths. Code is copied into agent-home/codoop-plugins/codoop-cast, with discovery links in agent-home/skills.

Windows must permit symlinks. Failure reports/preserves the bundle without enabling developer mode or self-elevation. Bundle existence is not discovery. Open a new/restarted host session and actually invoke setup/produce; until then this is file-install validation only.

Upgrade with the same command. Preflight rejects unrelated same-name skills before copying. Models/voices/projects/shared data are not deleted. No automatic uninstall/migration command.

## First initialization

Open the selected content folder and ask:

> Initialize codoop-cast with Chinese as my default artifact language. Check first and install only needed features. Keep content here and reuse one shared location for models/environments.

Setup saves output_language. Language-only setup downloads no models; speech/rendering prepares features when first required. The Windows launcher can privately bootstrap uv/Python without uninstalling system Python or changing PATH. First downloads need network/disk; explain actual location/size.

Windows shared data defaults to `%LOCALAPPDATA%/codoop-cast`, with explicit other-drive overrides: [layout](27-shared-data-layout.md). Content has report/script/assets/voice/subtitles/scenes/exports versions; never initialize it in installed plugin code.

## First video

> Use my reference recording to make a Chinese beginner-friendly video about my chosen topic. Portrait 1080×1920, avatar placeholder. Handle research, narration, assets, speech, subtitles and HTML animation automatically; export MP4. Omit punctuation at subtitle cue ends.

Supply the actual recording path or choose an existing voice. No fixed-length manual crop; the agent prepares a suitable clip. No training/fine-tuning. Unreliable initial recognition needs correct reference text, not silent acceptance of an incorrect transcript.

The agent creates the project, retains sources/stable identities, prepares media, aligns actual speech and returns a real MP4 path. Visuals/captions/avatar/aspect are adjustable; screenshots/plans are not final videos. After listening/viewing, request edits directly:

> Replace the image in the second scene; keep everything else.
>
> Make it landscape and reuse speech/subtitles.
>
> This pause is unnatural; redo this passage.

Asset edits reuse research/speech. Audio edits require new caption/timeline checks. Registered versions are retained rather than overwritten.

## Completion criteria

Complete files, host discovery and setup readiness are separate steps. End-to-end acceptance also needs actual speech, alignment, checked scenes and playable MP4. English listening, AMD/macOS, additional hosts/clean machines require independent records, not extrapolation from NVIDIA.

Native procedures follow the current host; public-marketplace listing is not claimed. Official references checked 2026-10-18: [OpenAI packaging](https://developers.openai.com/plugins/build/plugins), [Claude Code installation](https://code.claude.com/docs/en/discover-plugins), [Cursor plugins](https://prod.cursor.com/docs/plugins). Host documentation is not evidence this plugin installed successfully.
