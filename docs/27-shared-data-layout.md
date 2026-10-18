# 共享数据目录规范

共享数据根由 Agent 和运行时管理，用户不需要手工创建目录。默认 Windows 位置为 `%LOCALAPPDATA%/codoop-cast`；本机此前指定的是 `E:/codoop-cast-data`。选择顺序为 CLI 全局 `--root`、`CODOOP_CAST_HOME`、平台默认路径。目录本身不要求固定名称，内部格式保持一致。

## 固定结构：版本 1

```text
codoop-cast-data/
├── data-layout.json                 # 目录格式版本和受管理目录清单
├── config.json                      # 共享偏好，如 output_language 和 feature 配置
├── python/                          # uv 管理的私有 Python 发行版
├── envs/
│   ├── voice/                       # GPT-SoVITS 配音环境
│   ├── alignment/                   # 字幕对齐环境
│   ├── authoring/                   # 结构化创作、校验环境
│   └── video/                       # 浏览器渲染环境
├── engines/
│   └── gpt-sovits/                  # 锁定版本的上游源码及上游要求的资源
├── models/
│   ├── faster-whisper-small/
│   └── qwen3-forced-aligner-0.6b-hf/
├── tools/                           # uv.exe、ffmpeg.exe 等共享工具
├── browsers/
│   └── video/                       # Playwright 管理的固定浏览器版本
├── features/
│   ├── voice.json
│   ├── alignment.json
│   ├── authoring.json
│   └── video.json                   # 安装状态、资源版本、完整性记录
├── voices/
│   └── <voice-id>/                  # 32 位小写十六进制 ID
│       ├── voice.json              # 声音身份、文本、语言和资源路径
│       ├── original.<extension>     # 用户参考录音的副本
│       ├── reference.wav           # 自动选取的推理参考片段
│       ├── reference.json          # 片段选择信息
│       └── transcription.json      # 有执行识别时保存
├── jobs/
│   └── <job-id>/                    # 32 位小写十六进制 ID
│       ├── job.json                # 状态、输入身份、实际输出与错误
│       └── ...                     # 按任务种类保存输入、分段音频、对齐结果等
├── logs/                           # setup 日志及带 task ID 的业务日志
├── cache/
│   ├── downloads/                  # 校验过的下载包
│   ├── tmp/                        # 子进程 TEMP/TMP 与临时解包
│   ├── uv/
│   ├── pip/
│   ├── huggingface/
│   └── nltk/                       # 工具管理的缓存
└── locks/                          # 安装、GPU、配置等运行锁
```

目录按功能需要创建，setup 不预建所有空目录，也不提前下载全部模型。上游工具内部的文件名、Python 环境结构、浏览器版本目录保持原生格式，不强行重命名。GPT-SoVITS 要求放在源码树中的模型继续保留原位，由资源清单与完整性检查管理，不复制另一份到 models。

## 命名和归属

- 插件管理的固定目录使用小写 ASCII；复合名称用连字符。
- 环境、浏览器和状态以已注册 feature 名称命名；新增 feature 复用现有顶层分类，不在根目录另起一套数据树。
- 声音与任务使用稳定 ID，不使用用户姓名、话题或易变显示名做存储目录。
- 引擎任务内部文件由对应适配器管理：历史 `narration-<id>.wav/json`、`segment-<id>.wav`、原稿和配音文本仍有效；消费者读取 job.json 的实际路径，不能猜测文件名或依赖目录排序。
- 最终报告、稿件、素材、字幕、场景与视频保存在内容项目，按 stage/vNNN 管理。共享 jobs 可保留引擎输出和交接副本，但不取代项目中的正式产物。
- 不在共享数据根保存内容项目，也不把个人声音、模型或任务日志提交到插件仓库。

## 生命周期

voices、jobs、config.json 是持久数据，不作为普通缓存自动删除。features 是安装证明，不能手工将状态改为 ready。cache 可重建，但不能在任务运行期间盲目清空；本版不提供自动清理命令。locks 由运行时释放，不能仅因文件存在就判断可删除。

python、envs、engines、models、tools、browsers 为可重新安装资源，但修复应由共享 setup 按清单执行。不能删除整个共享根来修复一个 feature，不能因为缓存大就顺便删除用户声音或任务。

## 兼容和检查

setup 在旧数据根添加 `data-layout.json` 格式标记，保留已有资源、路径、未知文件及声音/任务记录。doctor 只读显示目录布局、标记状态和未知根级条目，不自动删除或迁移。遇到不支持的布局版本会明确报错，不覆盖未来版本。

更改 `--root` 或环境变量只是选择另一个根，不迁移现有数据。当前任务/声音记录可能包含绝对路径，因此不承诺直接移动目录就能继续运行；迁移工具不在本次范围。启动脚本会把显式 `--root` 同时用于 uv/Python 引导和后续运行，避免分散创建数据。

权威目录清单位于 `runtime/codoop-cast/castlib/data_layout.py`。新增读写位置必须同时更新该清单与本文，而不能临时在根目录创建无归属的文件夹。
