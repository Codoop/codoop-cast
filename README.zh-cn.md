# codoop-cast

[English](README.md) | [简体中文](README.zh-cn.md)

本地优先的社交媒体知识口播内容制作工具。将话题调研、口播稿撰写、声音克隆与配音、字幕对齐和视频制作组织为可独立使用的模块，并支持组合为批量制作流程。

当前版本：[v0.1.0-alpha.3](docs/zh-cn/releases/v0.1.0-alpha.3.md)（预发布）。

当前阶段：声音、字幕与 HTML 视频制作的 alpha 实现及本机验证。已有 setup/research/script/voice/subtitles/storyboard/assets/scenes/video/produce 十个 skills；原生 Agent 安装与其他硬件兼容性仍需分别验证。使用方法与限制见[声音复制运行说明](docs/zh-cn/08-running-voice.md)及[字幕运行说明](docs/zh-cn/16-subtitles-running.md)。

当前配音默认使用 GPT-SoVITS v2Pro，保存原稿和独立配音文本，通过保守的标点处理引导停顿。新任务不再叠加固定段间静音；旧任务继续使用创建时记录的模型与间隔。方案和验证见[停顿对比](docs/zh-cn/11-pause-comparison.md)。

分发定位：开源 Agent 插件，以 skills 为用户入口，配套本地执行脚本和按需依赖安装。用户主要用自然语言完成任务，不需要部署 HTTP 服务。

产品范围以用户完成内容制作所需为准，不按底层库的功能清单扩展。配音仅提供参考声音克隆与稿件转音频；不提供训练、微调或训练数据管理，也不将其列为后续路线。模型及推理参数由插件管理，用户不需要理解它们。

## 快速开始

把完整仓库交给 Agent，告诉它：“安装 codoop-cast，默认产物用中文，按需要准备环境”。在独立内容文件夹中提供话题和参考录音，就可以要求它完成调研到 MP4；素材和中间文件由 Agent 管理。

安装步骤、备用安装器和首次制作示例见 [安装与首次制作](docs/zh-cn/28-install-and-first-video.md)。当前能力、原生宿主安装及干净机器验证的具体状态见 [Alpha 发布状态](docs/zh-cn/29-release-readiness.md)。项目代码采用 [Apache-2.0](LICENSE)，第三方资源边界见 [THIRD_PARTY.md](THIRD_PARTY.zh-cn.md)。当前为 Alpha，原生宿主安装和干净环境完整验收仍待完成。

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [声音复制运行说明](docs/zh-cn/08-running-voice.md) | 当前实现、运行方法、依赖来源和限制 |
| [声音复制验证记录](docs/zh-cn/09-voice-validation.md) | 本机实际推理、局部重做与尚未验证的范围 |
| [字幕与对齐实施计划](docs/zh-cn/12-alignment-implementation-plan.md) | 初始实施计划；最新实现见字幕运行说明 |
| [独立 Skills 与交接契约](docs/zh-cn/13-skill-contracts.md) | 各 skill 职责、标准化视频脚本、依赖引用与局部重做 |
| [最小制作包结构](docs/zh-cn/14-production-schema.md) | JSON Schema 草案、72 秒贯穿示例和验证边界 |
| [本地对齐验证](docs/zh-cn/15-alignment-validation.md) | 纯中文字幕预览、混排未通过项与实际朗读映射缺口 |
| [字幕 Skill 与规范化映射](docs/zh-cn/16-subtitles-running.md) | 最新实现：混排映射、独立字幕入口、通用 setup 与剩余限制 |
| [批量队列运行说明](docs/zh-cn/24-batch-running.md) | 多项目顺序执行、错误隔离、恢复与汇总报告 |
| [单项目工作流运行说明](docs/zh-cn/23-produce-running.md) | 产物复用、执行计划、失败恢复、拼装与最终导出 |
| [稿件到配音适配](docs/zh-cn/22-script-audio-adapter.md) | 保留段落身份、双文本、实际前端映射与字幕交接 |
| [口播稿运行说明](docs/zh-cn/21-script-running.md) | 自然口播写作、来源关联、版本交付及估算时长 |
| [项目目录与文件命名](docs/zh-cn/20-project-layout.md) | 固定目录、版本、当前选择、依赖登记与项目命令 |
| [话题调研运行说明](docs/zh-cn/19-research-running.md) | 联网/本地资料调研、证据关联、报告导出与验证边界 |
| [视频 Skills 运行说明](docs/zh-cn/18-video-skills-running.md) | 三个独立入口、按需环境、真实时间轴与安装验证 |
| [首个 HTML 动画视频样例](docs/zh-cn/17-html-video-validation.md) | 标准分镜、真实时间轴、横竖屏 HTML 与本地 MP4 渲染原型 |
| [统一初始化 Skill 设计](docs/zh-cn/07-setup-skill-plan.md) | 所有功能共用的按需安装、配置与修复入口 |
| [Agent 与硬件兼容计划](docs/zh-cn/06-compatibility.md) | 参考 codoop-flow 适配 Agent，分阶段评估 NVIDIA、AMD 与 Mac |
| [开源插件与使用体验](docs/zh-cn/05-plugin-experience.md) | Skill 划分、按需安装、数据目录与发布验收 |
| [整体计划](docs/zh-cn/01-plan.md) | 产品范围、开发顺序、里程碑与待定事项 |
| [技术选型](docs/zh-cn/02-technology.md) | 推荐方案、备选项、取舍与验证要求 |
| [工作流程与数据约定](docs/zh-cn/03-workflow.md) | 模块依赖、项目产物、时间轴和任务恢复 |
| [GPT-SoVITS 实施计划](docs/zh-cn/04-voice-implementation-plan.md) | 第一个任务的范围、本地调用、实施步骤与验收 |
| [话题调研](docs/zh-cn/modules/research.md) | 从话题和资料生成通俗、有来源的报告 |
| [口播稿撰写](docs/zh-cn/modules/script.md) | 从报告生成适合朗读的稿件 |
| [声音与配音](docs/zh-cn/modules/voice.md) | 声音档案、TTS、质量检查 |
| [字幕与对齐](docs/zh-cn/modules/alignment.md) | 真实音频时间戳、字幕导出 |
| [视频制作](docs/zh-cn/modules/video.md) | 分镜、素材、模板、头像占位和渲染 |

## 设计约定

- 每个模块支持独立输入、独立输出和单独重做，不要求从话题开始运行。
- 模型推理、资料处理和渲染优先在本地完成；最新话题检索允许联网。
- 以实际生成的音频为时间依据，字幕与画面共用时间轴。
- 保留中间产物与来源，支持修改、缓存和失败恢复。
- 依赖按功能锁定；硬件及宿主兼容性以实际验证记录为准。

已跑通“确认口播稿 → 本地配音 → 对齐字幕 → HTML 动画视频”。分镜与画面可先于配音完成，精确时间轴在真实音频对齐后编译。调研 skill 已支持来源关联与报告导出；口播写稿已支持报告来源关联与本地导出；单项目编排与 Agent 驱动的顺序批量队列已接入。

### 产物语言

项目文档提供 en、zh-cn 两套版本；skills 内的指令与参考资料只维护英文。Skill 指令统一为英文；产物语言由 setup 保存的 `output_language` 控制，支持共享默认、项目/批次覆盖及本次任务覆盖。用户只需告诉 Agent 需要的语言。详见 [语言配置](docs/zh-cn/25-language-configuration.md)。

### 自动素材管理与共享数据

素材由 Agent 根据分镜自动准备、复用和记录来源，无需用户管理清单。支持已有文件、本地代码图示及宿主可用的生图能力；替换素材仅影响画面和导出。详见 [Agent 素材管理](docs/zh-cn/26-agent-assets.md)。模型、工具和声音档案位于独立共享数据根，视频素材和成片保存在内容项目。

共享运行目录的固定结构、命名、持久数据与缓存边界见 [共享数据目录规范](docs/zh-cn/27-shared-data-layout.md)。setup 按需建立目录并兼容已有数据，doctor 提供只读布局检查。

公开 skill 采用 `codoop-*`，例如 `codoop-setup`、`codoop-research`、`codoop-voice`、`codoop-produce`，与 codoop-flow 的入口风格一致。见[命名与升级兼容](docs/zh-cn/30-skill-naming.md)。

制作视频前读取共享/项目配置中的语言、横竖屏、分辨率、帧率、字幕样式和头像位置，再固定到 output-profile.json；本次要求可单独覆盖，见[制作配置](docs/zh-cn/31-production-configuration.md)。
