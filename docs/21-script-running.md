# 口播稿 Skill 运行说明

> 状态说明：本文保留对应开发阶段的计划或验证记录。当前已实现能力与发布缺口以 [Alpha 发布状态](29-release-readiness.md) 为准；首次使用见 [安装指南](28-install-and-first-video.md)。

2026-10-17：新增 codoop-cast-script，独立接收标准调研报告或用户的 UTF-8 Markdown/纯文本报告，由 Agent 写稿，复用本地 authoring 环境进行校验与导出。不要求先调用调研，不安装声音模型，也没有新增 HTTP 服务。

## 用户行为

用户可以说“把当前报告写成一份口播稿”“控制在一分钟左右”“保留这些重点，改得更自然”。Agent 从项目配置读取当前报告，或使用明确提供的外部报告；根据受众与篇幅组织解释，交付可直接审阅的稿件。没有指定时长时不强加目标。

写作遵守事实、数字、单位、条件、归因、推断及争议边界，避免夸大开场、虚构经历和空泛收尾。参考 Humanizer-zh 的自然表达原则，但不分发其整份 skill，也不强制用户额外安装。项目内的中文口播指引独立随包提供，不承诺任何 AI 检测结果。

## 固定产物

```text
script/vNNN/
  version.json        # 项目登记生成
  script.json         # 带稳定段落 ID、display_text、spoken_text、claim_ids
  script.md           # 易读正文，制作说明单独放在正文后
  script.txt          # 纯展示/原稿文本，不带标题、引用或制作备注
  spoken.txt          # 纯朗读文本；默认与展示文本相同
  script-source.json  # 输入报告与脚本摘要、相对位置及脚本身份
  checks.json         # 结构、来源关联、时长估算及限制
  inputs/             # 实际来源报告及声明的证据摘记
```

新稿件在 data.source 中固定报告 artifact_id/revision，外部文档则固定原文件 SHA-256。这个字段对现有 script schema 是可选扩展，旧字幕、分镜和视频样例继续有效；新写稿导出要求它存在。报告式输入的每个段落需要真实存在的 claim_ids；没有结论元数据的外部报告使用空列表，并标注未独立核验。

段落修改保留其稳定 ID，拆分/合并生成新 ID 并在 provenance 说明关系。稿件修改增加自身 revision；不能为了配合目录 vNNN 而改动所有输入对象的修订号。

## 命令

通过 scripts/cast.ps1 或兼容 Python 运行 runtime/codoop-cast/cast.py；全局 --root 在子命令前。

```text
script validate --script-file <草稿/script.json> --source-file <report.json或报告.md或报告.txt>
script export --script-file <草稿/script.json> --source-file <报告文件> --output <项目/script/vNNN> [--target-seconds 60]
script validate --script-file <已导出目录/script.json>
project register --directory <项目目录> --stage script --version vNNN --depends-on research=vMMM
```

导出使用新目录并保持旧结果；导出稿自带可读取的来源副本，移走原始资料后仍可验证。登记和选用遵循项目规范；稿件等待审阅时保留已有选用版本，不把新候选直接冒充已确认稿。

命令不调用模型、不自动创作，也不能仅靠有效 claim ID 证明正文没有改错事实。Agent 必须对照源报告复核数字、条件和表达。来源报告为 partial 或外部未核验时，在检查和制作说明中继续明确体现。

## 时长与下游

篇幅估算统计 spoken_text 中 Unicode 字母/数字，除以假定速率。默认每秒 4 个字符是透明的编辑假设，不是实测模型参数；可用 --characters-per-second 改变。它忽略停顿与实际数字/英文读法，对混排文本尤其粗略。--target-seconds 只记录目标，不能把估算冒充实际达到时长；Agent 应根据目标调整稿件，最终时长以真实配音为准。

storyboard prepare --script-file 能完整保留脚本身份和段落 ID，已实际验证。声音 CLI 当前仍只接受文本：默认以 script.txt 作为原稿，实际前端规范化由声音任务记录。如果 spoken.txt 有特殊读法，不能悄悄替换原稿并丢弃展示文本及段落关联；保留 ID 与双文本的声音适配器仍待实现。本次没有新增 TTS 接口，也没有将本次稿件实际合成为配音。

自然标点保留在口播文本中用于语义和停顿；字幕尾部去标点仅适用于字幕显示，不提前删掉稿件标点。写稿不分配最终字幕时间和分镜秒数。

## 验证记录

- 新增 12 项写稿契约测试，覆盖来源保留与可移植导出、原稿身份保留、过期报告、错误结论引用、重复/空段落、外部资料未核验、禁止伪造结论 ID、保留的报告被改动、partial、分镜导入、输出保护和非法时长参数。
- 普通测试 50 项、契约测试 35 项，共 85 项通过。
- 八个 skill 的格式检查通过；备用安装目录中的 script validate 可读取新导出的自包含稿件，不依赖原草稿路径。
- 已用现有字幕时间轴调研报告生成三段口播，保存到示例项目 script/v002，并登记 research/v001 依赖。v001 用于测试目标时长记录；v002 是不指定目标时长的候选稿，估算约 41.5 秒，不代表实际配音长度。未将任何候选稿标为用户已审阅选用。
- 旧生产包契约测试继续通过，原有八类视频产物没有因来源扩展而增加必选依赖。

剩余：稿件风格和节奏需要用户阅读反馈；完整串联还需保留稿件身份的配音适配、素材 skill 与编排/批量任务。本阶段的格式校验不等于通用的事实一致性评测。


2026-10-17 后续更新：结构化 --script-file 配音、双文本范围及原始段落 ID 还原已实现。前文关于“尚无稿件配音适配”的限制以[稿件到配音适配](22-script-audio-adapter.md)为准；读法压力输入存在的对齐失败也记录在该文中。
