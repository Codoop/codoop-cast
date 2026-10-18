# Skill naming

[English](30-skill-naming.md) | [简体中文](../zh-cn/30-skill-naming.md)

Public entry names follow [codoop-flow](https://github.com/Codoop/codoop-flow/tree/main/skills): `codoop-<capability>`, without repeating the plugin product name. The plugin itself remains `codoop-cast`; its runtime, data directories, CLI commands and project formats are unchanged.

| Previous entry | Current entry |
| --- | --- |
| codoop-cast-setup | codoop-setup |
| codoop-cast-research | codoop-research |
| codoop-cast-script | codoop-script |
| codoop-cast-voice | codoop-voice |
| codoop-cast-subtitles | codoop-subtitles |
| codoop-cast-storyboard | codoop-storyboard |
| codoop-cast-assets | codoop-assets |
| codoop-cast-scenes | codoop-scenes |
| codoop-cast-video | codoop-video |
| codoop-cast-produce | codoop-produce |

Use `codoop-setup`, not `codoop-init`, so it can coexist with codoop-flow's initialization entry. Directory names, SKILL.md name, default-prompt invocations, display names, cross-references and newly created workflow instructions use the same convention. Skill documents stay English.

Repeat the fallback installer to expose new names. After successful installation it removes only old discovery symlinks pointing into this plugin's own bundle. It preserves other plugins, unrelated paths, old bundled code, voices, tasks and projects. If a new name is already occupied by another skill, installation stops before copying; it never overwrites that entry. Native plugin users update through their host and refresh discovery using that host's supported procedure.

Old workflow plans retain their immutable contents/hashes. Runtime status maps their stages to current public skill names when returning the next actions. This is a routing compatibility rule, not a rewrite of historical files or a duplicate set of deprecated skills.
