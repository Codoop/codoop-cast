# 批量队列运行说明

[English](../en/24-batch-running.md) | [简体中文](24-batch-running.md)

2026-10-17：在已有 codoop-produce 中加入顺序批量模式，不新增一个重复的编排 skill。宿主 Agent 驱动每个项目的单项目流程，队列保存状态与交接，全部管理代码使用标准库，不新增模型、搜索服务或后台常驻进程。

## 目录与命名

```text
<用户指定的批次目录>/
  cast-batch.json
  projects/
    project-<12位ID>/
      cast-project.json
      research/v001/
      script/v001/
      ...
  reports/
    v001/batch-report.md
    v002/batch-report.md
  .cast/locks/
```

一个条目对应一个内容项目。新话题自动创建稳定英文目录，以话题作为显示名称；用户无需取文件名。已有项目可直接引用，不移动其文件。批次目录必须在单个内容项目之外，各项目的版本与 .cast/runs 状态继续独立。

cast-batch.json 固定记录批次 ID、模式、条目 ID、项目身份及位置、目标、话题、共享/单条需求文本、状态、运行历史、尝试次数、错误和产物指针。现有项目指针优先相对批次目录保存，可用 ../ 指向用户明确选定的外部项目；不同 Windows 磁盘使用绝对指针。这与制作包内的素材路径不同：素材仍不能越出制作包。移动整批文件时须保留外部路径关系，不能把绝对跨盘引用说成可自动迁移。

新格式为 schemas/cast-batch.schema.json，不是视频八类制作包的必选对象。批次文件不放进单个视频的 production/ 里。

## 用户入口

用户可以提供多个话题，或要求继续若干已有项目。Agent 将真实要求保存为队列，不要求用户手工配置 JSON。共享要求（已选声音 ID、画幅、分辨率、受众、时长、联网范围等）可通过 --brief-file 保存，单个项目可有自己的需求快照。只记录实际要求，不自行补上未确定的配置。恢复时读取这些记录，不只依赖聊天记忆。

```text
batch create --directory <批次目录> [--name <显示名>] [--brief-file <共享要求.txt>]
batch add --directory <批次目录> --topic <新话题> [--brief-file <单条要求.txt>]
batch add --directory <批次目录> --project <既有项目的绝对路径> [--target exports] [--force voice]
batch next --directory <批次目录>
batch status --directory <批次目录>
batch defer --directory <批次目录> --item <条目ID> --message <具体原因> [--needs-input]
batch retry --directory <批次目录> --item <条目ID>
batch pause --directory <批次目录>
batch resume --directory <批次目录>
batch cancel --directory <批次目录>
batch report --directory <批次目录> [--output <新的报告.md>]
```

--project 的相对参数按命令工作目录解析，Agent 应尽量传绝对路径。原需求文件内容在创建/入队时复制保存；之后改动原文件不会暗改已经计划的批次。更换规格时创建明确的新批次并按变化范围使用已有项目/强制重做，保留旧批次记录。

## 执行与恢复

每次 batch next 最多交出一个 active 项目及其 produce run_id。重复调用返回同一项目和运行，不重复启动业务任务。Agent 再调用现有单项目技能，完成校验、登记和 checkpoint。队列观察到 run 完成后保存成品链接，继续后面的项目；有效成品可直接复用。

没有业务进程由 batch next 启动，也不把创建队列算作视频已经生成。默认串行，不要求多个 Agent 并行占用 GPU。宿主 Agent 仍负责调研、写稿、画面制作及实际业务工具调用。

失败或信息不足会保留原因；确认没有仍在运行的步骤后释放条目，继续独立项目。需要输入时可汇总询问，不为一个条目无谓阻塞其余已授权工作。retry 是明确的有界操作：计划仍有效时复用原运行；输入已变则保留旧 run_history 并重规划。已完成项目若后来被改动，会变为 needs_replan，不偷偷重做。

正在执行的步骤不能被直接 defer。应先通过所属 skill 核对并取消/记录失败。若项目或状态文件丢失，队列默认保留 active 槽位；只有确实检查过实际任务已停止后，Agent 才可使用 defer --worker-stopped 并记录原因。该参数是调用方的显式断言，程序没有因此自动核对操作系统所有进程；不能用它绕过已知仍运行的步骤。

pause 阻止新工作，不杀死正在运行的任务；cancel 取消未执行条目，活动项目保持可见并要求实际取消/核对。resume 只恢复队列模式，不自动重跑已取消条目；需要明确 retry。暂停与取消状态保存在磁盘，不会因聊天继续就丢失。

## 状态与报告

命令 status=ready 表示命令成功；批次结果看 batch_state 和条目状态。

| 条目状态 | 含义 |
| --- | --- |
| pending | 尚待处理 |
| active | 当前项目，最多一个 |
| succeeded | 目标已完成且当前证据有效 |
| failed | 有具体失败原因，可核对后重试 |
| needs_input | 缺少必要信息 |
| needs_replan | 项目/选用版本/文件变化，须重新检查 |
| cancelled | 已取消，不自动恢复执行 |

批次 complete 表示所有条目成功；needs_attention 表示待执行项已处理，但有未解决条目。报告默认写入新的 reports/vNNN/batch-report.md，保留历史报告；列出实际成功产物和未解决原因。项目视频仍在其 exports/vNNN/video.mp4，不为出报告再复制一份视频。

## 验证记录

- 新增 22 项批量测试，以及 1 项批次 Schema 状态转换契约测试；普通测试 101 项、契约测试 40 项，共 141 项通过。
- 覆盖新话题项目、两个成品复用、单活动项/重复取任务、失败后继续、重复项目身份、暂停/恢复、取消不误重启、原运行重试、运行中不可跳过、项目改动、跨磁盘指针、未知工作进程显式核对、需求快照保存和历史报告保护。
- 实际批次包含两个已确认项目：43.73 秒竖屏字幕时间轴视频，以及导入的 72 秒横屏知识视频。后者的独立制作包通过既有八类 Schema 和跨文件验证。
- 两个项目经 batch next 识别有效成品并完成，状态为 2 succeeded；没有重生成配音或重渲染视频。汇总报告已生成。
- 本轮实际演示验证的是多个现有项目的复用和队列记录；新话题入队、失败继续等用确定性测试验证，没有额外编造话题来声称“已连续从零制作多个视频”。

尚待验证：更多新话题的实际批量创作质量、长时间宿主中断恢复及更多硬件/原生安装。不是后台无人值守服务，不自动发布社媒。素材自动管理已接入，见[素材管理](26-agent-assets.md)；开源发布许可整理仍待完成。
