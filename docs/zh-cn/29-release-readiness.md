# Alpha 发布状态

[English](../en/29-release-readiness.md) | [简体中文](29-release-readiness.md)

更新：2026-10-18。此文是当前发布状态入口；编号较小的计划、实验和验证记录保留历史事实，不应据其旧“尚未实现”描述判断今天的能力。

## 已具备

- 10 个英文指令 skill：setup、research、script、voice、subtitles、storyboard、assets、scenes、video、produce。
- 本地中文声音克隆与配音、实际音频对齐、字幕末尾去标点、HTML 动画到横竖屏 MP4；声音训练不在范围内。
- 结构化报告、来源关联稿件、稳定段落身份、展示/朗读双文本、版本化产物。
- 单项目恢复和 Agent 驱动的顺序批量队列；自动素材准备、来源记录及视觉变更局部重建。
- 共享语言配置、项目覆盖、共享数据目录格式标记、按需私有环境。
- 完整副本备用安装、路径含中文/空格的隔离验证；不等于原生宿主或干净机器完整验收。

## 发布前待完成

| 项目 | 当前状态 | 完成证据 |
| --- | --- | --- |
| 项目许可证 | 已选择 Apache-2.0 | 根目录 LICENSE、NOTICE 与 THIRD_PARTY.md 已添加 |
| 第三方代码、模型、字体和媒体许可 | 待集中整理 | 按实际锁定资源分别核对；不能以代码许可替代模型许可 |
| Codex/Claude Code/Cursor 原生安装 | 待逐宿主验收 | 宿主版本、安装方式、skill 发现与实际执行记录 |
| 干净 Windows NVIDIA 机器 | 待完整验收 | 非管理员、中文/空格路径、首次下载、重复 setup、第一条 MP4 |
| 更新与中断恢复 | 已有本机测试，待干净机器补验 | 更新后声音/作品保留；实际长任务中断后的恢复结果 |
| 全新话题批量成片 | 待完整质量验收 | 多个全新话题从调研到视频，覆盖失败隔离与素材变更 |

AMD、macOS 和英文配音人工试听列为后续兼容验证，不阻止把范围明确的 Windows NVIDIA alpha 交给测试者，但不得写成已支持。当前没有自动投稿、数字人口型、独立完整剪辑器、自动数据迁移或清理器。

## 打包边界

交付完整 skills、runtime、scripts、schemas 及宿主所需清单；说明和示例按需要附带。排除 work、私有录音、共享数据、缓存、Python 环境、下载权重和任务日志。先检查仓库/发布包实际内容，再生成 release；本阶段不自动提交、推送、发布或变更已选许可证。

测试报告要分别说明结构测试、实际模型推理、实际渲染及人工听看范围。自动化测试数不能替代干净环境或宿主安装结论。最新维护者测试可通过两组入口复现：

```text
python -m unittest discover -s tests
<authoring-python> -m unittest discover -s tests/contracts
```

authoring-python 是 setup 管理的 authoring 环境解释器，含锁定的 jsonschema 依赖；不要要求用户安装全局开发依赖来使用插件。
