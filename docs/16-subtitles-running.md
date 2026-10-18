# 字幕 Skill 与规范化映射

2026-10-17：已实现 codoop-cast-subtitles、alignment 通用 setup 注册和本地 CLI；Windows + NVIDIA 本机 alpha 验证通过。未发布，不声称原生 Agent 安装或所有语言/硬件已经验证。

## 用户入口

用户说“给刚才的配音生成字幕”，Agent 复用明确的已完成配音任务；也支持直接提供本地音频和稿件，不要求先安装或使用 voice。字幕环境独立准备，不启动 HTTP 服务。

```text
doctor --feature alignment
setup --feature alignment
subtitles generate --job <speech-job-id> --output <new-directory>
subtitles generate --audio <local-file> --text-file <utf8-transcript> --output <new-directory>
task status --job <subtitle-task-id>
```

所有命令通过 scripts/cast.ps1 或 Python 调用 runtime/codoop-cast/cast.py。沿用相同数据根目录；输出为新目录，拒绝覆盖。取消在分段之间检查；字幕任务尚不支持 resume，重新生成会保留旧任务。

## 实际朗读与显示文字

配音适配器观察本次推理实际调用的前端 preprocess，保存其 norm_text；不解析调试日志、不二次推测读法、不重跑前端。原函数在成功或异常后恢复。记录在每次 attempt 中，导出只引用当前选定 attempt 的规范化文本与映射。

原稿、TTS 输入配音稿、TTS 内部规范化稿是不同层次。例如“99.5元”可以规范为“九十九点五元”；字幕仍显示原来的数值写法。日期和数字按不可分组映射，ASCII 连续 token 保持完整，避免 CPU/GPU/SRT 分裂为单字母字幕。不能可靠映射的改写明确报错；不会通过替换其他内容来伪造覆盖。

归一化输入包含数字的变换只支持已定义的数字朗读字符集合；其他别名、单位替换、特殊读法、混合大小写转换等不保证支持。不把这个保守映射声称为通用文本规范化器。强制对齐仍不能证明音频没有漏读或读错。

字幕尾部隐藏标点，句内标点及百分号等语义符号保留。显示规则不修改音频时间。字幕输出有精度分组警告时保留原始预测；不补造独立字词时长。

## 输出交接

- script.json：段落展示文本和实际规范化朗读文本。
- audio.json 与 media/narration.wav：实际音频、分块样本偏移和朗读范围引用。
- alignment.json：字词/显示组时间与字幕条目，span_basis=display_text。
- checks.json：实际音频 SHA-256、引擎版本、覆盖和异常。
- subtitles.srt、raw-alignment.json、raw-units.json：交付字幕及可追查证据。

artifact_id 按字幕任务生成，彼此引用一致。音频跨度引用 spoken_text；对齐显示跨度引用 display_text，二者不可混用。新输出目录包含相关音频副本，后续无需解析聊天记录或推测源文件路径。

这是可独立消费的字幕制作包片段，不是具有八类产物的完整视频包。当前段落由音频分块适配形成；与未来内容稿件的稳定段落 ID、多对多分块映射尚需工作流适配器，不宣称已经支持 script.json 直接输入。

## 本机验证

规范化混排声音任务 a665971cbf574ebe9ac2590c3e10dc31 与旧混排任务输出 WAV 的 SHA-256 相同，确认观察前端没有改变该样例的声音。日期 2026年10月17日、金额 99.5元、CPU/GPU、1080P 和 SRT 均建立规范化映射。

正式字幕任务 6c35d53b9087416495cc33e0555dfb90：35.22 秒、12 条字幕，正文覆盖与时间结构检查无错误，保留两个零时长字组合警告。数字与英文 token 不被拆开显示。新版混排预览待用户观看确认，不能扩大之前纯中文样例的主观验收。

后续用户已观看新版混排预览并确认正常，该样例主观验收通过；不扩展为所有外部输入均已验收。

外部音频独立入口任务 f0b2b3057f3444eb8585af609914e0c2：19.27 秒纯中文音频及稿件，实际解码、对齐和 SRT 导出通过。该入口不调用 voice setup。

37 项测试通过（31 项普通测试、6 项制作包契约测试），setup/voice/subtitles 三个 skill 格式检查通过。setup 重复执行直接复用 ready 环境。实际输入范围、音频内容与分块清单在推理前核对，不能仅凭时长相同接受被更换的音频。

在带空格和中文的隔离 agent-home 完成备用完整 bundle 安装，复制后的 CLI 能读取 alignment 状态；实际交付的 script/audio/alignment 通过 JSON Schema、引用、展示正文覆盖及尾部标点检查。这不是 Codex/Claude/Cursor 原生插件安装验收。

## 尚未覆盖

历史混排配音没有前端记录时返回明确原因；可重新配音获得记录，不把日志解析当成正式来源。历史纯中文允许存储文本回退。

外部音频单窗口目前不超过五分钟；自动长音频窗口和文本定位未实现，明确报告能力限制，不要求用户自己剪切。外部数字读法未知时可提供可信的单独 spoken-text-file，否则对齐异常需核查，不保证自动恢复。模型加载成功或 SRT 导出不代表完全同步，仍需预览。

AMD/Mac、干净用户机器、原生宿主安装、复杂画幅字幕排版、完整漏读检测、HTML 场景和最终投稿视频尚未验收。


2026-10-17 后续更新：结构化 --script-file 配音、双文本范围及原始段落 ID 还原已实现。前文关于“尚无稿件配音适配”的限制以[稿件到配音适配](22-script-audio-adapter.md)为准；读法压力输入存在的对齐失败也记录在该文中。
