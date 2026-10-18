# 稿件到配音与字幕的身份保留适配

> 状态说明：本文保留对应开发阶段的计划或验证记录。当前已实现能力与发布缺口以 [Alpha 发布状态](29-release-readiness.md) 为准；首次使用见 [安装指南](28-install-and-first-video.md)。

2026-10-17：声音入口新增 --script-file，结构化稿件可以直接配音并交给字幕、分镜定时，不再必须先压平成纯文本。

## 实际流程

```text
script/vNNN/script.json
  → speech generate --script-file
  → voice/vNNN/narration.wav + narration.json + script.json
  → subtitles generate --job <speech-job-id>
  → 原始 script.json + audio.json + alignment.json + subtitles.srt
  → 原稿分镜锚点与实际音频编译时间轴
```

保留原稿 artifact_id、revision、段落 ID、claim_ids、来源及展示/朗读文本。TTS 的实际前端规范化文本单独记录，不用它覆盖原稿。纯文本入口保持原有行为；没有提供过的段落来源不会被事后猜出来。

## 分块和双文本

本版按段落准备配音，一个段落可拆成多个块，不跨段落合并。100 字符是内部拆块目标，不限制用户整篇稿件长度；显式读法或英文数字整体分组不被拆开，必要时单块可超过目标。参考声音原始录音的用户输入方式不变。

每个配音块记录：

- script_spans：原段落 spoken_text 的 Unicode codepoint 半开范围。
- display_span：原段落 display_text 的范围。
- display_text、spoken_text：这块对应的原始双文本。
- text：经过既有保守标点停顿处理、实际提交给 TTS 的文本。
- requested_mapping：展示文本到请求朗读文本的映射。
- normalized_text、text_mapping：实际 TTS 前端文本，以及展示到该实际文本的映射。

数字和标点转换继续使用保守映射。真正改变字形的读法需要显式 pronunciation_spans，例如某个多音字用同音字引导发音；Agent 根据已约定读法填写 display_start/display_end/spoken_start/spoken_end，用户不必计算索引。未声明的无关改写、越界或非单调范围会拒绝，不能凭字符串相似度猜测读法。

组合范围只提供整体时间，不宣称里面每个字都有独立可靠时间。显式改写的意义和读法仍需 Agent/用户检查，索引正确不证明读法合适。

## 交付与重做

```text
speech generate --script-file <script/vNNN/script.json> --voice <voice-id> --output <voice/vMMM/narration.wav>
subtitles generate --job <speech-job-id> --output <subtitles/vKKK>
speech retry --job <speech-job-id> --segment <one-based-index>
```

结构化导出自动保存 narration.wav、narration.json、script.json、original.txt、narration.txt，拒绝覆盖任一目标。narration.json 仍是引擎清单，不能直接改名为标准 audio.json；它含私有分块路径，不是可在任意机器完整恢复的推理缓存。

结构化任务的 retry 可以重生成相同文本，但拒绝 --text 替换。内容修改应先生成新稿件 revision，再创建配音任务，避免音频偷偷偏离已经规划分镜的稿件。创建、恢复和导出时检查固定稿件指纹及分块范围。

字幕阶段先在音频块内部对齐，再将范围还原到原段落。最终 script.json 与输入对象相同。audio.json 的 spoken_text/script_spans 指向原稿请求朗读文本；可选 normalized_text 保存真实前端输入，text_mapping 为该块局部展示文本到前端文本的映射，display_span 标明其在原段落的位置。旧版本音频产物不强制增加这些字段。

字幕尾部去标点继续有效，口播原稿本身的自然标点保留。没有可靠时间范围时不输出伪造字幕。

## 本机验证

- 12 项新测试覆盖长段落拆分与原文范围、数字读法、显式同音字范围组合、模糊改写拒绝、越界、分组不被拆开、块时间还原、稿件及分块改动、重复段落、尾部标点、结构化导出副本、拒绝替换固定文本。普通测试 62 项、契约测试 35 项，共 97 项通过。
- 真实稿件：示例项目 script/v002（三个段落、来源关联），使用用户此前确认的声音生成 43.73 秒配音。声音任务 97a1c5b1f9fc45b8be9ac228cf15a5d8。
- 最新字幕任务 874f52ac58a74cfba5e1f1285bd90e6a，保存 subtitles/v002。issues/warnings 均为空，原始稿件对象、三个段落 ID 与结论引用完全保留。三类 JSON Schema、原朗读文本切片一致性、三个分镜的原段落锚点编译均通过。
- 示例项目 voice/v001 与 subtitles/v002 已登记对 script/v002 的依赖，没有把机器生成成功当作用户已经听看确认。
- 额外长段落与特殊读法压力输入（内部 work/structured-audio-check）：长段落拆为两个块，原稿映射保留。显式读法及数字映射成功，但实际对齐模型在末段返回三个零时长单元；任务 44b72b56ff234a0f89287c6c4f802aee 返回 needs_input，保留诊断并拒绝导出 SRT。没有通过补造时间来伪装该压力输入已验收。

当前已完成结构交接，但不承诺所有读法都能取得可靠对齐。主要样例仍需播放检查音色、读法、漏读与字幕同步。后续完整编排、独立素材管理与批量任务尚未实现；本轮没有重新渲染成品视频。
