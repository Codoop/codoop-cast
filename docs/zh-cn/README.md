# 项目文档

[English](../en/README.md) | [简体中文](../zh-cn/README.md)

用户与维护者文档在 en、zh-cn 中一一对应；skills 内的指令与参考资料只维护英文。历史文档保留当时状态，当前能力以发布状态文档为准。

## 文档目录

- [整体计划](01-plan.md)
- [技术选型](02-technology.md)
- [工作流程与数据约定](03-workflow.md)
- [声音复制与配音 Skill 实现计划](04-voice-implementation-plan.md)
- [开源插件与 Agent 使用体验设计](05-plugin-experience.md)
- [Agent 与硬件兼容计划](06-compatibility.md)
- [统一初始化 Skill 设计](07-setup-skill-plan.md)
- [声音复制：当前实现与运行说明](08-running-voice.md)
- [声音复制 Alpha 验证记录](09-voice-validation.md)
- [音色改善：同稿对比记录](10-voice-comparison.md)
- [停顿对比实验](11-pause-comparison.md)
- [字幕与对齐实现计划](12-alignment-implementation-plan.md)
- [独立 Skills 与工作流交接契约](13-skill-contracts.md)
- [最小制作包结构 v0.1.0](14-production-schema.md)
- [本地对齐验证记录](15-alignment-validation.md)
- [字幕 Skill 与规范化映射](16-subtitles-running.md)
- [首个 HTML 动画视频样例](17-html-video-validation.md)
- [视频 Skills 运行说明](18-video-skills-running.md)
- [话题调研运行说明](19-research-running.md)
- [内容项目目录与文件命名规范](20-project-layout.md)
- [口播稿 Skill 运行说明](21-script-running.md)
- [稿件到配音与字幕的身份保留适配](22-script-audio-adapter.md)
- [单项目工作流 Skill 运行说明](23-produce-running.md)
- [批量队列运行说明](24-batch-running.md)
- [Skill 英文化与产物语言配置](25-language-configuration.md)
- [Agent 自动素材管理](26-agent-assets.md)
- [共享数据目录规范](27-shared-data-layout.md)
- [安装与首次制作](28-install-and-first-video.md)
- [Alpha 发布状态](29-release-readiness.md)
- [字幕与对齐模块](modules/alignment.md)
- [话题调研模块](modules/research.md)
- [口播稿撰写模块](modules/script.md)
- [视频制作模块](modules/video.md)
- [声音与配音模块](modules/voice.md)
- [codoop-cast v0.1.0-alpha.1](releases/v0.1.0-alpha.1.md)

- [Skill 命名规范](30-skill-naming.md)

- [按配置制作视频](31-production-configuration.md)

- [codoop-cast v0.1.0-alpha.2](releases/v0.1.0-alpha.2.md)

## 维护约定

同一次修改同步更新两个语言版本；保持命令、ID、哈希、日期和验证边界一致。LICENSE/NOTICE、schema 键和固定产物文件名不翻译。证据样例保留原件，英文只作单独阅读对照，不更改已固定哈希的来源正文。在仓库根目录运行 `python scripts/check_docs.py` 检查。
