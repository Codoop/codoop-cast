# 技术选型

[English](../en/02-technology.md) | [简体中文](02-technology.md)

状态：GPT-SoVITS 已确定为首版配音引擎，尚未部署实测；其他选型仍为候选。项目能力与许可依据前期对官方资料的调研；正式集成前再次核对所选版本、模型卡、权重和依赖许可，不将“本地部署”等同于“可商用”或“完全离线”。

## 运行与应用结构

| 层 | 建议 | 原因及边界 |
| --- | --- | --- |
| 操作入口 | Agent skills + 本地 CLI | 开源分发，具体宿主清单经安装验证后确定 |
| 本地业务模块 | Python 函数与类 | 直接调用模型与文件处理能力，不引入 HTTP 框架 |
| 项目与任务元数据 | SQLite | 初期单机使用，不提前引入数据库集群 |
| 大文件 | 本地项目目录 | 音频、素材和视频与数据库分开保存 |
| 模型运行环境 | 各引擎独立环境或进程 | 避免 PyTorch、CUDA、Transformers 版本冲突 |
| 批量执行 | 初期单工作进程与持久化任务 | GPU 阶段排队，后续有吞吐需求再增加队列系统 |

项目仅本地使用，不启动 HTTP 服务或监听端口。一般模块直接调用 Python 函数；GPT-SoVITS 若需要独立依赖环境，则通过常驻本地子进程执行任务，以标准输入输出传递 JSON 消息，大文件通过本地路径交接。日志写入 stderr 或文件，不混入结构化消息。

## 语言模型与调研

- [Ollama](https://github.com/ollama/ollama)：候选本地语言模型运行器，模型大小根据硬件实测确定。
- [SearXNG](https://github.com/searxng/searxng)：候选自部署搜索入口；搜索依然访问外部搜索源，可用性受网络和搜索源限制。
- [Crawl4AI](https://github.com/unclecode/crawl4ai)：候选网页正文提取工具；遇到登录、反爬或失败页面应返回失败状态，允许用户导入资料。
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher)：调研编排参考，不作为首版强依赖。

初期自建有界流程：拆问题 → 检索 → 提取正文 → 保存证据 → 生成报告。设置检索数量和执行时间上限，不做无限循环探索。

## 口播润色

参考 [Humanizer-zh](https://github.com/op7418/Humanizer-zh) 与 [Humanizer](https://github.com/blader/humanizer)。它们是写作规则，不是独立模型。集成时核对许可、记录来源和所用版本，将适用规则纳入口播流程，并增加事实保留约束。

## 本地 TTS

| 候选 | 用途 | 选型判断 |
| --- | --- | --- |
| [CosyVoice](https://github.com/QwenAudio/CosyVoice) | 中文参考声音克隆与口播 | 后续备选，首版不集成 |
| [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | 参考声音克隆 | 后续备选，首版不集成 |
| [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) | 参考声音克隆配音 | 用户已选定为首版引擎；仅集成推理所需能力 |
| [ChatTTS](https://github.com/2noise/ChatTTS) | 对话式表达实验 | 暂不作为默认引擎；公开权重有非商业限制，不能将随机音色复用视为指定人物克隆 |

前期核对的 [CosyVoice 3 指定权重](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512) 与 [Qwen3-TTS 0.6B Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) 模型卡标注 Apache-2.0。该结论不自动适用于同项目全部资源。

试听比较：同一参考声音、同一稿件；记录音色相似度、数字及多音字错读、漏读与重复、段落连贯性、耗时和显存峰值。不预先承诺最低显存或实时速度。

## 对齐与识别

- 首轮对齐候选：[Qwen3-ForcedAligner](https://github.com/QwenLM/Qwen3-ASR)，输入真实音频与已知文本。
- 对齐备选：[WhisperX](https://github.com/m-bain/whisperX)，需核对中文对齐模型及依赖。
- 配音核查候选：[faster-whisper](https://github.com/SYSTRAN/faster-whisper) 或 Qwen3-ASR；识别差异用于提示与重试，不直接覆盖已确认稿件。

## 视频渲染

| 方案 | 适用性 | 决策 |
| --- | --- | --- |
| [Remotion](https://github.com/remotion-dev/remotion) | 动态排版、逐步图解、参数化模板、预览 | 优先验证视觉效果；采用前核对[专门许可证](https://www.remotion.dev/docs/license) |
| [MoviePy](https://github.com/Zulko/moviepy) + [FFmpeg](https://ffmpeg.org/) | 拼接、叠加、简单动画与编码 | 备选；若选定则避免同时维护两套首版渲染逻辑 |

优先导出 MP4（H.264 视频、AAC 音频）与独立 SRT；画幅和帧率由制作配置确定。FFmpeg 构建及编码器许可按实际分发方式核对。

## 整套项目参考

- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)：主题到短视频的流程参考。
- [NarratoAI](https://github.com/linyqh/NarratoAI)：已有视频解说与剪辑的流程参考。

首版不直接合并整套代码；先验证是否需要复用。外部素材与在线模型依赖必须逐项识别，不能假定这些项目默认全本地运行。
