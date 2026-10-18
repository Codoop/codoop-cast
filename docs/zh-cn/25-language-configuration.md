# Skill 英文化与产物语言配置

[English](../en/25-language-configuration.md) | [简体中文](25-language-configuration.md)

参考 codoop-flow 的 `output_language` 约定：初始化时保存偏好，当前任务的明确要求优先。codoop-cast 的 9 个 skill、配套指令与 Agent 元数据统一使用英文；用户对话和产物不因此变成英文。

## 配置位置

共享默认值保存在私有数据根目录的 `config.json`，与现有 features 设置共存。项目或批次目录可以保存 `.codoop-cast/config.json`，子项目就近继承。文件使用 JSON，以复用现有运行时和 Python 3.10 标准库，不增加 TOML 依赖。

```json
{
  "schema_version": 1,
  "output_language": "zh-CN"
}
```

插件仓库提供 `codoop-cast.config.example.json`。用户通常只需告诉 Agent“默认用中文”“这个项目用英文”，由 setup 写入配置，不需要自己编辑文件。该文件是所有 skill 的共享配置入口，后续初始化设置可以扩展字段；重复 setup 保留已有设置和未知字段。

优先级：当前任务明确指定 → 最近祖先目录的配置 → 私有共享默认配置 → 旧项目 defaults.language → auto。配置不会修改对话语言。

## 命令

以下为 CLI 子命令，通过安装位置的 `scripts/cast.ps1` 调用；Python 入口为 `runtime/codoop-cast/cast.py`。全局 `--root` 仍位于子命令之前。

```text
setup --output-language zh-CN
setup --directory <content-project-or-batch> --output-language en
config show --directory <content-project-or-batch>
config show --directory <content-project-or-batch> --language en-US
setup --feature voice
```

不带 feature 的 setup 只保存配置，不安装模型或业务环境；带 feature 时仍复用该共享设置。`config show --language` 仅解析本次覆盖，不保存。

`auto` 由 Agent 按当前明确要求、输入内容、对话语言依次判断；运行时不猜测用户对话。Agent 在新的 report/script 的 data.language 中记录具体语言，并把具体语言作为本次参数传给需要语言的命令。

research/script 的 validate/export、speech generate、外部音频的 subtitles generate、纯文本的 storyboard prepare、produce plan、batch report 支持 `--language`。结构化口播与已有语音任务始终以自身记录的语言为准；不能通过覆盖参数把中文音频伪装为英文。

## 产物和工作流

报告正文、口播、屏幕文字、字幕、制作说明按照目标语言生成。引用原文、专有名词、来源快照、地址、ID、schema 键与固定 ASCII 文件名按需保留。运行时检查声明与目标是否一致；真正的翻译由 Agent 完成，配置不会替代正文翻译，也不能自动判断每一句的实际语言。

产物的 data.language 是版本的一部分。切换语言后，创建翻译后的新版本，保留已有确认版本，并重新生成受影响的配音、字幕、画面和导出。produce 记录目标语言；配置语言变化会要求重新规划。本次明确覆盖的运行不受随后默认值变化影响。不同语言的已选报告/稿件不会被新计划直接复用。

旧 report 没有 language 字段时仍按历史中文格式处理；新的 Agent 产物应显式填写。旧工作流计划仍可读取。旧批次没有任何语言配置时保留历史中文报告格式；显式 auto 则需 Agent 解析后传参。

## 当前支持边界

内置的报告、稿件、批量报告、分镜审阅标签支持简体中文和英文。其他语言可由 Agent 根据 `castlib/locale.py` 的英文标签生成 `.codoop-cast/locales/<tag>.json`，保留全部格式占位符；缺少完整翻译时明确报错，避免悄悄混入中文标签。

Agent 可撰写其他语言的内容；当前配音/对齐适配层仅接通 zh/en，并在模型初始化之前拒绝其他语言或未解析的 auto。英文参数传递和导出已做自动化验证；本次没有重新合成英语音频，未确认英语音色、发音与对齐质量。参考录音的语言是独立设置，不随产物配置改变。

统一规则位于 `skills/codoop-setup/references/language.md`，所有 skill 都必须先遵守它，不另外维护各自的语言默认值。

参考：

- https://github.com/Codoop/codoop-flow/blob/main/codoop_flow.toml.example
- https://github.com/Codoop/codoop-flow/blob/main/skills/codoop-init/SKILL.md
