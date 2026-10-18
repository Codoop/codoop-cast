# 第三方资源

[English](THIRD_PARTY.md) | [简体中文](THIRD_PARTY.zh-cn.md)

codoop-cast 原创代码使用 Apache-2.0；这不改变依赖、下载模型、字体、来源摘录或用户媒体的许可。仓库分发适配器、依赖版本与资源清单，不打包模型权重或已安装环境。

## 资源清单

| 资源 | 来源与版本记录 | 分发边界 |
| --- | --- | --- |
| GPT-SoVITS 源码与预训练声音资源 | [上游](https://github.com/RVC-Boss/GPT-SoVITS)，runtime/codoop-cast/resources-voice.json | 在私有 setup 中下载；源码及各项预训练资源分别遵守上游条款 |
| Whisper 识别资源 | resources-voice.json 及 runtime/codoop-cast/ 中的固定依赖 | 下载资源不属于本项目许可授权范围 |
| Qwen3 对齐器 | [模型仓库](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B-hf)，resources-alignment.json | 固定 revision、模型卡与资源下载到共享数据根 |
| uv 与私有 Python | [uv](https://github.com/astral-sh/uv)，启动资源清单 | 独立可执行文件/运行时许可；本仓库不重新分发系统 Python |
| PyTorch 与 Python 依赖 | requirements-*.txt、constraints-*.txt、feature setup | 安装进私有环境；许可声明以实际发行包为准 |
| Playwright 与 Chromium | [Playwright](https://github.com/microsoft/playwright)，resources-video.json | 浏览器及供应商声明属于下载发行包 |
| FFmpeg | 功能安装及 imageio-ffmpeg 依赖 | 条款取决于实际下载的构建与编码器；不受本项目许可替代 |
| 系统字体 | 输出配置与宿主系统 | 不随包分发；使用者需具备相关权利或选择合适替代字体 |
| Humanizer 参考 | [Humanizer](https://github.com/blader/humanizer)、[Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 可选链接，不内置这些 skill，不要求安装 |
| 调研证据快照 | 示例/项目报告中的来源 URL 与元数据 | 属于来源内容而非原创代码；保留的示例标注实际来源 |

这份清单不代表许可审计已经完成，也不授予第三方内容的使用权。重新分发权重、可执行文件、字体或打包环境之前，应保留并核对实际固定版本的许可及声明。Alpha 源码发布不宣称所有上游资源具有相同商用条款。

用户参考录音、声音档案、生成旁白和制作素材不包含在源码发行中。Agent 管理的素材记录实际来源及已知许可；未知信息应保持未知，不能标注为已获批准。
