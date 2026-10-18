# 声音复制：当前实现与运行说明

[English](../en/08-running-voice.md) | [简体中文](08-running-voice.md)

当前实现为 alpha：已有 setup/voice skills、共享本地 CLI、GPT-SoVITS v2 推理适配器、声音保存复用、分段重做和 WAV 自动拼接。硬件和模型实际验证结果另见验证记录；不能把已有代码视为所有宿主与设备均已支持。

本机验证结果见[验证记录](09-voice-validation.md)。

## 使用入口

向 Agent 描述：“用这段声音读这篇稿子。”提供原始单人录音即可，插件在本地转写并自动选取适合模型的参考语句，保存后可复用。无需手动裁切或填写整段文字；识别不可靠时会返回所选片段与文字请用户确认。已知有多人时需先明确目标人物，当前不自动区分说话人。支持中文和中英混排口播，不提供训练或微调。

Windows 维护者可运行（仓库根目录）：

```powershell
./scripts/cast.ps1 doctor --feature voice
./scripts/cast.ps1 setup --feature voice
./scripts/cast.ps1 voice create --audio 'D:/audio/original.m4a'
./scripts/cast.ps1 speech generate --text-file 'D:/scripts/narration.txt'
```

这不是要求普通用户手动执行的流程；skill 负责按意图调用。无可用 Python 时，Windows launcher 下载经过校验的私有 uv 并准备 Python；不改变全局 PATH。通过已有 Python 3.10+ 直接执行 `runtime/codoop-cast/cast.py` 也是可用入口。

默认数据目录是 `%LOCALAPPDATA%/codoop-cast`。如需其他磁盘，在所有命令的子进程环境中使用同一 `CODOOP_CAST_HOME`；已有数据不会因改变目录而自动迁移。首次安装包括约 2.3GB 模型下载（含本地识别模型）、CUDA PyTorch 和其他依赖，还需要解压及缓存空间。以资源清单和磁盘检查为准。

命令参数和 skill 执行规则见 [配音调用参考](../../skills/codoop-voice/references/execution.md)。

## Agent 分发

仓库提供 Codex、Claude Code、Cursor 插件清单及 marketplace 清单。优先使用宿主原生插件安装；公开仓库发布后的安装指令需在实际宿主验证，当前不承诺已完成商店发布或原生宿主兼容测试。

备用安装器：

```text
python scripts/install_skills.py --agent codex --dry-run
python scripts/install_skills.py --agent codex
```

也可选择 `claude` 或 `cursor`。安装器把完整 skills/runtime/scripts 放到用户 Agent 目录下的独立 bundle，并创建 skill 发现链接，不修改模型数据目录。Windows 创建符号链接需要相应权限或开发者模式；如果失败，保留 bundle 并明确报错，可使用宿主原生插件安装。重复执行不会覆盖不属于该 bundle 的已有 skill。

## 实现边界

- 仅实现 Windows + NVIDIA 后端；AMD 与 Mac 仍按兼容计划评估。
- 普通业务流程不使用 HTTP，不启动 API 或 WebUI；依赖与模型首次下载仍需联网。
- 推理环境启用 Hugging Face 离线模式；语言和读音依赖若发生隐式下载，需要通过真实输入验证后纳入准备流程，不能仅凭模型加载宣布完全离线。
- 取消在段落边界生效；不承诺立刻打断当前推理。
- 分段、生成清单和历史尝试保存在数据目录，不要求用户手动管理。
- 状态使用原子写入 JSON 文件，首版没有引入 SQLite；后续确有索引需求再迁移。
- 字符读法、相似度、跨段自然度仍需要实际试听，当前不提供自动 ASR 质检。
- 参考素材转写使用 faster-whisper small 的 CPU int8 本地推理，和生成后 ASR 质检是不同环节；仅前者已接入。模型置信度只能辅助判断识别结果，不代表声音身份验证。
- 项目自有代码许可证待维护者确定；对外发布前补齐 LICENSE 和第三方许可，不将依赖权重自动视为自有许可。

## 依赖与来源

源码固定为 GPT-SoVITS `6df61f58e4d18d4c2ad9d1eddd6a1bd690034c23`，模型使用匹配 v2 权重。下载 URL、上游版本、大小与 SHA-256 保存在 `runtime/codoop-cast/resources-voice.json`。仅下载推理所需生成器和基础模型，不下载判别器等训练资源。

为免 Windows 用户安装 C 编译器，适配器将上游所需的 jieba_fast 分词接口映射到纯 Python jieba。保留上游代码与其许可，未将上游源码复制到发布仓库。安装中的 Lightning 等包属于上游推理导入所需依赖，不构成对用户提供训练功能。

## 验证命令

```text
python -m unittest discover -s tests -v
```

测试验证声音选择、结构化 CLI、路径处理、资源校验和音频拼接等确定性行为；真实模型验证另行记录，不能用这些测试代替。
# 当前默认策略（2026-10-17 更新）

新任务使用预训练 v2Pro，不训练用户声音。setup 自动准备并校验所需权重及说话人编码器，旧 v2 权重暂保留供历史任务恢复。首次升级会重新进行模型加载检查。

配音任务保存 `original.txt` 与 `narration.txt`，只对中文长句中的部分逗号和分号做句号提示，不增加或删除词语。普通短句不变。按最多 100 字分块，块内整段推理；模型片段附加间隔为 0.15 秒，导出不再叠加额外的 0.2 秒。停顿仍受模型预测影响，不能保证所有稿件都自然。

任务保存模型与合成策略，重做时沿用；没有新策略字段的历史任务保持原有行为。局部改稿保留原始输入，更新配音文本；每次尝试保存实际输入和音频，导出清单记录当前文本与模型。
