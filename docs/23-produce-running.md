# 单项目工作流 Skill 运行说明

2026-10-17：新增 codoop-cast-produce。用户在内容项目目录里提出目标，由宿主 Agent 调用各独立 skill，复用已确认产物，继续缺少或受影响的环节。没有新增在线服务、后台任务调度器或模型。

## 分工

Agent 负责理解目标、调研写作、分镜和画面创作、调用声音/字幕/导出工具及审阅结果。本地 produce 命令负责确定性计划、版本固定、状态记录、失败记录与制作包拼装。命令本身不会自主调用大模型完成整片创作，不能把计划已创建当成视频已生成。

独立 skill 保持独立。用户直接导入口播稿、配音或完整字幕包时，将其作为明确的有效入口，不要求补做此前环节。素材当前由 scenes 的 assets.json 和本地文件管理，不把未实现的独立 assets skill 加为必经环节。

## 执行计划

默认依赖：research → script → storyboard → assets；storyboard + assets → scenes，以及 script → voice → subtitles；scenes + subtitles → exports。一个有效的选中中间产物可以截断对上游的重新执行。计划先检查项目 current 和登记完整性，不通过最大版本号猜测输入。

```text
produce plan --directory <项目> [--topic <话题>] [--target exports] [--force voice]
produce status --directory <项目> --run <run-id>
produce start --directory <项目> --run <run-id> --stage <环节> [--job <任务ID>]
produce assemble --directory <项目> --run <run-id> [--output <新拼装目录>]
produce checkpoint --directory <项目> --run <run-id> --stage <环节> --version vNNN [--job <任务ID>]
produce fail --directory <项目> --run <run-id> --stage <环节> --message <具体原因> [--job <任务ID>] [--needs-input]
```

--topic 保存任务背景，不会把旧视频改个话题名称就当成新成品。实际更换话题应新建内容项目，或显式从 --force research 重新规划。仅改变配音时 --force voice 会重做配音、字幕和导出，保留未受影响的稿件和画面。target 可以停在调研、稿件等环节。

partial/invalid 输入进入 review 动作，不能当成完成输入自动跳过。需要修复、补齐或明确导入新版本后继续；不会默默删除旧结果。阶段开始只登记执行意图，不等于任务进程已经启动。尚在运行的阶段不能盲目再次启动；先核对实际 job 和日志。

## 固定目录和状态

```text
.cast/runs/<run-id>/
  plan.json      # 不变的执行计划、环节及复用决定
  state.json     # 阶段状态、已用版本、清单摘要、任务ID、尝试次数和事件
.cast/work/<run-id>/
  assembly/      # 选中产物的临时拼装
  <检查和预览>
exports/vNNN/
  video.mp4
  production/
  video-qa/
  version.json
```

计划本身校验摘要；已复用或已完成步骤固定其选用版本、登记清单及其实际文件完整性。选中版本改变、上游依赖改变或文件被改动时 workflow_state 为 needs_replan，不允许悄悄混入新输入。

状态查询的 status=ready 仅表示查询成功；实际工作流状态查看 workflow_state：pending、running、failed、needs_input、needs_replan、complete。checkpoint 要求阶段已启动、产物已登记为 ready，且实际依赖与当前计划一致；它选中该阶段产物并记录进度。最终视频还需成功的 rendered 报告与实际 MP4 摘要一致。以上不等于用户已审阅每一项内容或事实一定正确。

任务失败后保存具体原因与 job ID。依据所属 skill 支持的恢复方式处理，不重复生成有效上游；新输出使用新版本目录。没有进程自动复活能力，未登记进度前的中断需从共享数据根日志/任务记录恢复，不能把状态文件当作进程监控器。

## 拼装和导出

produce assemble 在 exports 阶段运行中接收计划选中的 scenes 与 subtitles：

1. 验证版本、文件和当前选择仍与计划一致。
2. 要求两边 script.json 对象完全相同，不凭“文字看起来一样”擅自替换身份或版本。
3. 核对实际旁白样本数、采样率，以及可用时的对齐音频摘要。
4. 仅复制声明的核心 JSON、HTML、素材、实际音频和相关字幕/检查文件；同一路径内容冲突时拒绝。
5. 输出新 assembly 目录和索引，随后调用既有 video compile/check/render。

业务环节专门校验和 Agent 内容审阅仍然必要。拼装命令不替代分镜规划、不编造音频，也不生成猜测的精确时间。

## 本轮实际验证

使用真实话题“字幕为什么需要时间轴”，从用户已确认的 script/v002、voice/v001 和 subtitles/v002 继续。没有重新搜索、写稿、配音或对齐。运行 888a0066af874c868d3234a41f1cfcfc：

- 复用既有稿件和字幕包，原始配音 SHA-256 保持一致。
- 创建三段主题画面：字幕出现时机、字幕时间卡、配音改变后的时间核对。独立分镜登记 storyboard/v001，画面登记 scenes/v001；不是固定框架的通用三页模板。
- 画面无声预览、真实时间轴检查及往返定位检查通过；抽查编码后的字幕画面，无越界或头像重叠。
- 成功导出 exports/v001/video.mp4：1080×1920、30fps、约 43.73 秒、H.264/AAC。全片解码通过，最终登记和 checkpoint 完成，工作流状态为 complete。
- 再次规划能够直接复用已导出视频，没有创建新配音/渲染任务。

本轮验证的是已有中间产物继续到 MP4 的真实路径；新项目从话题展开完整阶段链有确定性测试，但没有在同一次新运行中重复生成整套已有内容。新画面是待用户观看的本地草稿，不宣称自动取得审美/内容批准。

新增 17 项编排测试与 4 项拼装契约测试；普通测试 79 项、契约测试 39 项，共 118 项通过。覆盖输入版本/内容变动、计划改动、强制重做范围、外部入口、前置依赖、错误依赖、失败记录及重试、partial、重复启动、最终导出证据，以及不同稿件、素材路径冲突、音频样本不一致和源文件保持不变。九个 skill 格式检查通过。

仍待完成：批量队列、独立素材管理、更多宿主的原生安装验收、AMD/macOS 验证和开源发布前许可整理。特定读法的对齐失败边界仍以 docs/22 为准，编排不会绕过该失败伪造字幕。当前仅本地交付，不自动投稿社媒。


2026-10-17 更新：Agent 驱动的顺序批量队列已接入 produce，支持错误隔离、暂停/取消、显式恢复与版本化汇总报告。前文“批量尚未实现”的状态以[批量运行说明](24-batch-running.md)为准。
