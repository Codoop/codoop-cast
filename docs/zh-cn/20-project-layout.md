# 内容项目目录与文件命名规范

[English](../en/20-project-layout.md) | [简体中文](20-project-layout.md)

状态：2026-10-17，项目格式 0.1.0。新建内容项目使用本规范；原有独立制作包继续作为输入，不自动移动用户文件。七个已实现 skill 共用这套规则，安装包内的执行细节见 skills/codoop-cast-setup/references/project-layout.md。

## 目录结构

一个用户选定的文件夹对应一个话题或一条内容。项目根目录名称由用户决定，可用中文和空格；内部受管理的目录、文件使用固定英文小写和短横线。下面是完整格式，实际按需创建，不提前建立空业务目录。

```text
<用户选定的内容项目>/
├── cast-project.json
├── research/
│   └── v001/
│       ├── version.json
│       ├── report.json
│       ├── report.md
│       ├── checks.json
│       └── sources/<source-id>.md
├── script/
│   └── v001/
│       ├── version.json
│       ├── script.json
│       ├── script.txt
│       └── script.md
├── storyboard/
│   └── v001/
│       ├── version.json
│       ├── video-script.json
│       └── storyboard.md
├── assets/
│   └── v001/
│       ├── version.json
│       ├── assets.json
│       └── files/<asset-id>.<ext>
├── voice/
│   └── v001/
│       ├── version.json
│       ├── narration.wav
│       ├── narration.json
│       ├── original.txt
│       └── narration.txt
├── subtitles/
│   └── v001/
│       ├── version.json
│       ├── subtitles.srt
│       ├── alignment.json
│       ├── audio.json
│       ├── script.json
│       ├── checks.json
│       ├── media/narration.wav
│       └── raw/
├── scenes/
│   └── v001/
│       ├── version.json
│       ├── scene.json
│       └── files/index.html
├── exports/
│   └── v001/
│       ├── version.json
│       ├── video.mp4
│       ├── production/
│       │   ├── package.json
│       │   ├── script.json
│       │   ├── video-script.json
│       │   ├── assets.json
│       │   ├── scene.json
│       │   ├── audio.json
│       │   ├── alignment.json
│       │   ├── timeline.json
│       │   ├── output-profile.json
│       │   └── <清单引用的素材、HTML、音频与其他文件>
│       └── video-qa/
│           ├── render.json
│           ├── ffmpeg.log
│           └── 01-<scene-id>.png
└── .cast/
    ├── work/<task-id>/
    ├── jobs/<task-id>.json
    └── locks/
```

上方目录树保留初始格式示意；当前自动素材构建使用 `media/<sha256>.<ext>`，以[素材管理](26-agent-assets.md)中的后续实现为准。

各版本目录可以额外包含独立运行所需的输入快照，例如 storyboard 中的 script.json、assets.json、output-profile.json、package.json。这些副本保留输入原有 ID 与修订号，不成为另一份可随意修改的上游正文。所有辅助资源须按现有制作包规则登记。

script 的独立 skill 已实现，见[口播稿运行说明](21-script-running.md)；assets 已由 Agent 自动管理，见[素材管理](26-agent-assets.md)。.cast/jobs 为按需记录的任务引用，当前引擎的实际任务日志、模型、Python、浏览器缓存及跨项目声音档案仍在共享数据根，不在每个内容项目重复保存。

## 名称约定

- 项目根标记统一为 cast-project.json，不再混用 project.json。
- 上游内容脚本统一为 video-script.json，不使用 plan.json 或 storyboard.json 替代。
- 配音使用 voice，字幕与对齐使用 subtitles，最终输出使用 exports；新项目不混用 audio、alignment、renders 等目录别名。
- 每个环节独立使用 v001、v002……v999、v1000。版本号不得重用或重新编号，失败留下的编号可以跳过。
- 核心文件不加日期、话题名或“最终版”后缀；所属话题、环节和版本已经由外层目录表达。
- 来源摘记使用稳定 source ID，素材使用稳定 asset ID，扩展名反映实际格式。额外说明文件使用描述性的英文小写短横线名称。
- 引擎生成的原始诊断文件保留其格式与文件名，不重命名造成引用失效。截图沿用 NN-<scene-id>.png；多于 99 张时序号自然扩展。
- 文件内容用 UTF-8；清单内路径相对所在包/版本目录，以 / 分隔，不写开发者绝对路径或越出目录。现有声音引擎清单仍包含私有任务路径，暂不能宣称其完全跨机器复现。

## 当前版本与依赖

cast-project.json 保存项目 ID、显示名称、默认输出配置及 current。current 对每个环节记录明确选用的版本或 null。它是输入发现入口，不能凭“编号最大”或文件修改时间认定用户选中了新版。

每个已完成目录通过 project register 生成 version.json，记录该环节版本、ready/partial 状态、文件 SHA-256 和实际依赖的上游版本及其登记清单 SHA-256。目录版本与 JSON 对象 revision 含义不同：一次新的执行不等于所有输入对象都要升级修订号。

登记后的目录不再修改或追加文件；修订创建新版本。从旧版复制起草时不要复制旧的顶层 version.json。登记不自动选用，新版在本任务中已明确用作后续输入时再通过 project select 选中。普通任务成功不必额外增加确认；尚待用户审稿时保留原选用版本。

project status 的状态：

| 状态 | 含义 |
| --- | --- |
| missing | 该环节尚未选用版本 |
| ready | 选中版本的文件与已登记依赖一致，不代表事实或人工审阅通过 |
| partial | 明确作为资料不完整等部分结果交付 |
| stale | 使用的直接或间接上游版本与当前选用版本不同，需复核 |
| invalid | 文件缺失、变动、出现未登记文件，或依赖清单变化等异常 |

状态查询只检查并报告，不自动重做、替换或删除文件。project register 检查目录结构和完整性，不替代 research/storyboard/scenes/video 等环节的专门校验。

## Agent 执行方式

```text
project init --directory <内容项目目录> --name <显示名称>
project status --directory <内容项目目录或其子目录>
project path --directory <内容项目目录> --stage research
research export --report-file <草稿/report.json> --output <内容项目目录/research/v001>
project register --directory <内容项目目录> --stage research --version v001
project select --directory <内容项目目录> --stage research --version v001
# 下游登记时写入实际依赖，可重复 --depends-on：
project register --directory <内容项目目录> --stage script --version v001 --depends-on research=v001
```

项目命令本身不需要安装模型或 authoring 环境。project path 返回尚未创建的候选路径，不是并发预约；如输出已被其他进程占用，应重新取新路径，禁止覆盖。需要改写的草稿、预览与临时组合包放在 .cast/work/<task-id>/。

声音阶段当前 --output 只复制 WAV，Agent 还需从该任务返回的产物中复制导出清单并命名 narration.json，以及 original.txt、narration.txt。不要把 narration.json 直接改名为标准 audio.json；后者由字幕交接生成。

视频先编译到 exports/vNNN/production/，再渲染到 exports/vNNN/video.mp4；现有渲染器自动生成相邻 video-qa/。检查完成后再登记整个导出版本。横屏和竖屏使用不同 exports 版本，在各自 production/output-profile.json 保留准确配置；无需在文件名重复尺寸。

项目查找从任务指定目录向上寻找最近的 cast-project.json；没有标记时，在用户已指定的内容文件夹初始化。不要因为默认终端目录是插件源码，就把源码目录初始化成内容项目。没有指定可用目录时才询问位置。原有独立包导入时保持原文件，需要时把本次交付保存为项目的新版本。

## 实现与验证

已实现 project init/status/path/register/select；原有 project index --package 继续用于制作包哈希索引，二者职责不同。新增 cast-project 与 stage-version JSON Schema；项目管理运行时使用标准库检查，不为目录操作安装环境。

新增 13 项项目测试覆盖初始化复用、父目录发现、候选版本、显式选择、直接/间接过期、文件改动、未登记文件、缺文件、嵌套项目、非法版本、覆盖保护、partial 和整项目移动。现有普通测试共 50 项、契约测试 23 项，共 73 项通过。已用真实调研报告运行初始化、导出、登记、选中与状态查询；其他阶段的目录约定已接入 skill，尚未在新项目目录中逐个重新生成全部媒体。


2026-10-17 后续更新：结构化 --script-file 配音、双文本范围及原始段落 ID 还原已实现。前文关于“尚无稿件配音适配”的限制以[稿件到配音适配](22-script-audio-adapter.md)为准；读法压力输入存在的对齐失败也记录在该文中。


2026-10-17 更新：单项目 produce 编排 skill、运行计划/状态、版本固定及制作包拼装已接入。最新边界及真实续做验证见[工作流运行说明](23-produce-running.md)。


2026-10-17 更新：Agent 驱动的顺序批量队列已接入 produce，支持错误隔离、暂停/取消、显式恢复与版本化汇总报告。前文“批量尚未实现”的状态以[批量运行说明](24-batch-running.md)为准。
