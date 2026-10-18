# 安装与首次制作

[English](../en/28-install-and-first-video.md) | [简体中文](28-install-and-first-video.md)

当前为 alpha。本机 Windows + NVIDIA 已完成中文配音、对齐和 MP4 制作；完整副本安装脚本已做隔离验证。Codex、Claude Code、Cursor 的原生插件安装仍待逐宿主验收，不能把清单存在等同于已通过安装测试。

## 让 Agent 安装

将仓库或完整源码目录交给 Agent，说明：

> 帮我安装 codoop-cast，保留完整的 skills、runtime、scripts、schemas。检查我的 Agent 能否发现这些 skills，先不要下载声音模型。

不要只复制 SKILL.md，skill 需要同包运行时。插件不需要 HTTP 服务或 API key；联网调研和生图使用宿主已有能力，需要对应宿主具备工具。

维护者可在源码根目录使用备用安装器；以下 Python 指兼容的现有 Python 3.10+，安装器自身不负责安装 Python：

```powershell
python scripts/install_skills.py --agent codex --dry-run
python scripts/install_skills.py --agent codex
```

Claude Code 使用 `--agent claude`，Cursor 使用 `--agent cursor`。默认分别定位用户的 `.codex`、`.claude`、`.cursor`；使用自定义宿主目录时明确传入 `--agent-home <directory>`，不要猜测实际宿主配置目录。脚本将完整代码复制到 `<agent-home>/codoop-plugins/codoop-cast`，再把各 skill 的发现入口链接到 `<agent-home>/skills/`。

Windows 创建符号链接需要系统允许；失败时脚本会报告并保留完整副本，不会改动系统开发者模式或自行提权。不要把“副本已存在”当作 skill 已可发现。重启/新开宿主会话后，实际检查能否调用 setup 和 produce。未完成此项之前只记为文件安装验证。

升级使用同一安装命令。安装器在复制之前拒绝覆盖不属于该插件的同名 skill；它不清除模型、声音、项目或共享数据。不提供自动卸载/数据迁移命令。

## 首次初始化

在一个用户选择的内容目录打开 Agent，告诉它：

> 初始化 codoop-cast，默认产物语言用中文。先检查环境，需要什么再安装。内容放在当前目录，模型和环境复用一个共享数据目录。

Agent 使用 setup 保存 `output_language`；仅配置语言不下载模型。首次使用声音或渲染时才安装所需 feature。Windows 启动器可准备私有 uv/Python，无需卸载系统 Python 或修改 PATH。首次下载需要网络和足够磁盘空间，Agent 应说明实际目标位置和资源体积。

共享目录默认为 `%LOCALAPPDATA%/codoop-cast`，可显式指定其他磁盘。它包含模型、独立环境、声音档案、任务与缓存，详见[共享目录规范](27-shared-data-layout.md)。内容项目包含 report/script/assets/voice/subtitles/scenes/exports 等版本目录，不能在插件安装目录里初始化项目。

## 第一条视频

> 用我提供的参考录音，制作一条介绍“我给定的话题”的中文知识视频。面向小白，竖屏 1080×1920，头像先用占位。自动完成调研、口播稿、素材、配音、字幕和 HTML 动画，最后导出 MP4。字幕条目末尾不要标点。

提供参考录音的实际路径，或选择已有声音。录音不要求用户手动裁剪固定时长；Agent 准备合适的参考片段。不提供声音训练或微调入口。首次声音识别不可靠时，需要核对真实参考文本；不能把错误转写悄悄当作正确输入。

Agent 创建项目、保存来源和稳定稿件身份、自动准备素材，按实际配音生成对齐时间，最终返回真实 MP4 路径。画面、字幕、头像位置和画幅可按需调整，不能把预览截图或计划文件称为成片。用户听看后可以直接提出修改：

> 第二个画面的图片换一下，其他内容保持。
>
> 改成横屏，配音和字幕继续复用。
>
> 这句停顿不自然，重新做这一段。

素材变更不重做研究和配音；声音变化则重新检查字幕和最终时间轴。已登记版本保留，不覆盖旧作品。

## 安装完成的判定

安装文件齐全、宿主能发现 skill、setup 检查成功是不同的验证步骤。首次完整验收还需实际生成配音、对齐字幕、检查场景并导出可播放 MP4。英文配音听感、AMD/macOS、更多宿主和干净机器的完整流程仍需分别记录，不能套用本机 NVIDIA 结论。

原生安装方式以目标宿主当前版本为准，本项目尚未承诺已上架公共市场。2026-10-18 核对的官方参考：[OpenAI 插件打包](https://developers.openai.com/plugins/build/plugins)、[Claude Code 插件安装](https://code.claude.com/docs/en/discover-plugins)、[Cursor 插件](https://prod.cursor.com/docs/plugins)。这些是宿主文档，不是本项目安装成功的证明。
