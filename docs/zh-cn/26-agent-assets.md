# Agent 自动素材管理

[English](../en/26-agent-assets.md) | [简体中文](26-agent-assets.md)

用户描述视频或画面需求即可，不需要选择素材目录、填写清单、编写提示词或手工搬运文件。新增 `codoop-cast-assets`，供 Agent 自动调用，也支持独立准备素材集合。

## 自动选择和准备

Agent 根据分镜与场景需求，优先复用已有合适素材。图解、图表和装饰适合用 HTML/SVG 绘制时直接本地完成；需要位图时调用宿主已有的生图能力并检查实际结果。没有生图工具时优先采用合适的本地图示；特定人物照片、真实事件画面等不可替代内容缺失时，明确说明缺口，不伪造素材获取结果。

生图不内置新的本地扩散模型，也不强制用户购买服务。外部素材如被实际使用，需要记录真实来源和已知使用信息；未知许可不能标成已经核验。生成图作为示意，不作为事件照片或研究证据。画面文字遵守共享语言配置。

## 文件与版本

最终素材归入内容项目 `assets/vNNN/`，包含 `assets.json` 和 `media/<sha256>.<extension>`。共享的 `codoop-cast-data` 存环境、模型、工具、跨项目声音和引擎任务，不作为本条内容的素材仓库。

Agent 在 `.cast/work/<task-id>/` 写临时清单，声明稳定素材 ID、实际输入文件、来源、使用说明；可附生成器、提示词、作者、许可说明、来源地址和时间。CLI 复制实际字节并生成内容哈希，同内容、同扩展名的文件在一个集合内只复制一次。替换时复用素材 ID 和集合 artifact_id，增加 revision，生成新的版本目录。

```text
assets build --manifest-file <draft.json> --output <new-assets-version>
assets build --manifest-file <draft.json> --previous <old-assets.json> --output <new-assets-version>
assets validate --assets-file <collection>/assets.json
assets attach --assets-file <collection>/assets.json --package <mutable-scene-package>
```

这些命令不需要新增模型环境。清单格式见 skill 的 `references/execution.md`。空集合是有效完成状态：完全用代码生成的画面不必额外找图片。

attach 将素材复制进新的场景工作包，拒绝改写已登记版本及冲突文件。Agent 随后明确更新分镜、scene 引用、资源路径和 revision，再重新建立索引、校验与预览。CLI 不猜测创作意图，也不自动更改字幕或声音。

## 工作流

新流程增加 `storyboard → assets`，场景依赖 `storyboard + assets`；配音和字幕仍走原先独立分支。替换素材使用 `produce plan --force assets`，复用既有分镜、配音、字幕，只重新准备素材、生成画面和导出。纯画面样式变更可 `--force scenes`，继续复用素材。

已登记的旧场景包仍可直接复用，不强制迁移所有历史项目；旧计划保持原有步骤。新流程登记 assets 的实际分镜依赖，scenes 登记分镜和素材依赖，素材变化会使依赖它的后续版本过期。

此功能管理素材文件与交接，不意味着所有宿主已具备生图、联网素材搜索或许可核验能力；实际工具是否可用由 Agent 检查。最终视觉质量仍通过场景预览和成片检查确认。

## 共享数据目录

`codoop-cast-data` 是共享运行数据根目录，本机此前选择的是 `E:/codoop-cast-data`；名字可以不同。默认位置是 Windows `%LOCALAPPDATA%/codoop-cast`，可通过 `CODOOP_CAST_HOME` 或 CLI 的 `--root` 指定。setup 重用相同目录，不应每个项目另建一套。

这里包括私有 Python 环境、下载的 TTS/对齐模型、浏览器与 FFmpeg、声音档案、缓存和引擎日志/任务。独立于插件安装目录，因此更新插件无需再次下载全部资源；独立于内容项目，因此多项目可以复用。直接删除可能丢失声音档案与任务，或导致依赖重新下载。目前没有自动迁移/卸载命令，单纯修改路径不会迁移已有数据。
