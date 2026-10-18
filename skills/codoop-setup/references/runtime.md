# Shared local initialization

Resolve the real installed SKILL.md location, following discovery symlinks if present. Its two-parent directory is the complete plugin root. Invoke the absolute path to `scripts/cast.ps1` on Windows, or `runtime/codoop-cast/cast.py` with Python 3.10+ when already available. Resolve neither path from the user's working directory.

```text
doctor
doctor --feature <registered-feature>
setup --output-language <tag>
setup --directory <content-scope> --output-language <tag>
config show --directory <content-scope>
setup --feature <registered-feature>
```

`voice`, `alignment`, `authoring` and `video` are registered. Each uses its own private environment; authoring provides lightweight schema/plan operations, video installs pinned Playwright/Chromium and FFmpeg. alignment with external audio does not install voice. The registry in `runtime/codoop-cast/castlib/setup.py` provides feature checks and preparation; other features are added there when implemented. Generic setup does not run business tasks or create user content.

Default data root is the platform user data directory. Pass `CODOOP_CAST_HOME` in the child environment to choose a different root and reuse that same location for future commands. Changing it does not migrate existing data. Python CLI also accepts global `--root <directory>` before the subcommand. Do not change global PATH, interpreter registrations or shell execution policy.

PowerShell launcher can fetch pinned uv and prepare private Python without an existing Python installation. It requires network on first use; each feature installation separately prepares its declared resources. Quote local paths for the current shell, and prefer subprocess argument arrays over building command strings from user text.

stdout is JSON, stderr and data-root `logs/` contain progress/errors. Read the actual exit code and state. Wait using the host's long-running process support; do not report ready from a download-completed log. Repeated setup reuses a ready feature and installation resources; investigate concrete failures before retrying.
