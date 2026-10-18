# 视频 Skills 运行说明

[English](../en/18-video-skills-running.md) | [简体中文](18-video-skills-running.md)

> 状态说明：本文保留对应开发阶段的计划或验证记录。当前已实现能力与发布缺口以 [Alpha 发布状态](29-release-readiness.md) 为准；首次使用见 [安装指南](28-install-and-first-video.md)。

2026-10-17：将已验证的本地 HTML 渲染原型封装成三个独立 skill，接入共享初始化。本记录更新 docs/17 中“尚未封装”的历史状态。

## 用户入口

| Skill | 可以单独接收 | 交付 |
| --- | --- | --- |
| codoop-cast-storyboard | 口播文本或 script.json | 标准分镜、语义锚点、审阅稿、制作包索引 |
| codoop-cast-scenes | 分镜制作包 | 话题专属 HTML、场景清单、画面检查截图 |
| codoop-cast-video | 分镜、场景、真实音频和对齐包 | 真实时间轴、可编辑完整制作包、MP4 |

用户用自然语言表达任务，由 Agent 读取 skill、创作内容、调用本地工具。规划与画面设计由 Agent 完成，不是固定的十页模板算法；准备命令只导入口播并建立规范文件，不把空目录冒充成分镜生成。视频导出不需要 HTTP 服务。

## 按需初始化

共享 setup 已注册 voice、alignment、authoring、video。authoring 仅安装 jsonschema 及依赖；video 使用独立环境安装 Playwright 1.56.0、imageio-ffmpeg 0.6.0 和 jsonschema 4.23.0。Chromium Headless Shell build 1194 通过官方 Playwright 安装，校验主程序 SHA-256 后验证浏览器版本、离线启动与截图，并验证 FFmpeg 启动。固定版本和约束随 runtime 分发。

外部配音制作视频无需安装声音模型；仅规划无需安装浏览器。私有工具和缓存均位于同一配置数据根，初始化不改全局 Python、PATH 或驱动。Windows 本机已验证；AMD 与 macOS 未验证。渲染使用 CPU H.264 编码，不以 NVIDIA 作为视频编码的硬性要求。

## 本地命令

通过 scripts/cast.ps1 调用以下命令；也可使用兼容 Python 运行 runtime/codoop-cast/cast.py。全局 --root 位于子命令前。用户不需要手动执行或编辑这些文件，由 Agent 完成。

```text
storyboard prepare --text-file <口播.txt> --output <新的规划目录>
# 或导入既有 script.json，保持 artifact_id/revision/段落 ID
storyboard prepare --script-file <script.json> --output <新的规划目录>
project index --package <制作包目录>
storyboard validate --package <制作包目录>
scenes validate --package <制作包目录>
scenes check --package <制作包目录> --output <新的预览名称.mp4>
video compile --package <来源目录> --output <新的完整制作包目录>
video check --package <完整制作包> --output <新的检查名称.mp4>
video render --package <完整制作包> --output <新视频.mp4>
task status --job <任务ID>
task cancel --job <视频渲染任务ID>
```

check 只产出同名 -qa 目录的检查报告与截图，不生成 MP4。scenes check 在缺少音频时使用示意时间，带有“画面草稿”标记，禁止作为最终导出时间轴。video check 使用真实时间轴。取消在导出帧间生效，当前不支持断点续渲染。

若对齐结果包含已有的保守合并警告，仅在用户已经审阅同一音频/对齐结果后，才可对 compile 使用 --accept-reviewed-alignment；不能借此绕过非法时间范围。实际音频或稿件变更后需重新验证。

## 制作包与修改

JSON Schema 与运行时一同分发。Agent 编辑后显式调用 project index 更新哈希；版本号及引用由 Agent 正确维护，索引命令不会自动修复过期引用。验证区分分镜阶段和画面阶段，允许缺少后续产物。

HTML 实现 render-at-time-v1：configure、ready、renderAt、inspect 和 snapshot。所有动效由绝对时间重建；渲染时离线读取本地文件。CSS、JS、图片、字体等辅助资源需登记到 assets 清单，编译时才会被复制。具体界面、图形与动画由当前话题决定。字幕尾部不带标点，内部标点和有意义符号保留。

横竖屏、分辨率、帧率、字幕样式和头像位置存于 output-profile；HTML 需实现对应布局，不能只拉伸画面。当前默认头像为占位，未实现口型数字人。编译输出新目录并保留旧项目；局部修改无需重做声音或其他内容，但当前导出仍重渲染整片，没有分镜帧缓存。

先规划后配音的跨 skill 交接目前仍需 Agent 显式核对段落 ID 与版本；尚无自动保留规划稿段落 ID 的 TTS 适配器。建议复用字幕包的 script.json 进行精确配套，或由 Agent 正确协调引用，不能仅因文字相同就复用旧时间戳。

## 验证记录

- authoring/video 共享 setup 本机执行成功，重复 doctor 均 ready。
- 普通测试 37 项、契约测试 12 项，共 49 项通过；覆盖无音频规划、缺失实际音频、引用过期、未更新哈希、锚点越界与保留导入稿件身份等情况。
- 六个 skill 均通过 skill-creator 格式检查。
- 隔离的中文及空格安装目录中，备用安装器分发 schemas/runtime/scripts/skills，发现链接及安装后命令调用通过；未把该检查声称为所有宿主的原生安装验证。
- 独立水果主题 HTML、单场景、不同 DOM，无音频和对齐文件，画面检查及往返定位检查通过，截图已查看。
- 用户此前确认的横屏制作包，经公开 video compile 和 video render 命令导出 72 秒、1920×1080、30fps、2160 帧 MP4，全片解码通过；没有重新生成配音。导出保留运行报告、输入哈希与代表帧。

尚待实现：话题调研和口播撰稿 skill、完整工作流编排、批量队列、分镜缓存与自动失效管理、预规划稿到 TTS 的身份保留适配、真实头像素材流程、更多宿主原生安装与 AMD/macOS 验证，以及发布前许可证整理。Agent 内容创作质量仍需人工审阅。
