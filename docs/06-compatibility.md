# Agent 与硬件兼容计划

状态：规划与官方资料调研，尚未完成本项目实际安装及推理验证。优先顺序已由用户确定：Windows + NVIDIA → Windows + AMD → Mac。

## Agent：参考 codoop-flow

参考 [codoop-flow 安装文档](https://github.com/Codoop/codoop-flow/blob/main/docs/install.md) 及其仓库清单，采用多宿主薄层适配、共享 skills 与 runtime 的方式，不再将产品限定为仅支持 Codex。

| Agent | 计划分发方式 | 发布前验证 |
| --- | --- | --- |
| Codex Desktop / CLI | 插件清单与 marketplace 入口 | 安装、发现 skill、定位 runtime、执行本地任务 |
| Claude Code | 插件清单与 marketplace 入口 | 安装、发现 skill、定位 runtime、执行本地任务 |
| Cursor | 插件清单；复制安装作为备用 | 加载插件、发现 skill、定位 runtime、执行本地任务 |
| 其他 Agent | 支持相应 skill 格式时，复制 skills 与 runtime | 按实际宿主验证，不把复制成功视为可用 |

主线设计覆盖前三类宿主，发布时分别标注测试结果和版本；具体安装命令随实际包验证后给出。其他宿主属于尽力兼容，不预先宣称通用支持。

规划结构：

```text
.codex-plugin/plugin.json
.claude-plugin/plugin.json
.cursor-plugin/plugin.json
<宿主需要的 marketplace 清单>
skills/<skill-name>/SKILL.md
runtime/codoop-cast/              # 共享 CLI、业务模块、引擎适配器
scripts/                         # 安装与打包入口
docs/
```

以上为未来包布局，本次不创建清单或代码。共享运行代码只保留一份，skill 按自身安装位置解析 runtime，不依赖当前工作目录。复制安装必须复制共享 runtime 并保持可解析的相对位置；不能只复制 SKILL.md。

借鉴分发方式，不复制 codoop-flow 的业务限制：本项目不要求用户作品目录是 Git 仓库，也不要求票据目录。安装引导必须提供 Windows 可执行路径，不能要求 Windows 用户先安装 Bash 才能使用备用安装器。

## 硬件支持分阶段验证

| 顺序 | 平台 | 验证路径 | 当前状态 |
| --- | --- | --- | --- |
| P0 | Windows + NVIDIA | CUDA、兼容依赖、参考声音克隆 | 开发机 RTX 3070 Ti 8GB 已识别，尚未推理验证 |
| P1 | Windows + AMD | 核对具体显卡/系统与原生 PyTorch 支持，再验证完整 GPT-SoVITS 推理 | 调研阶段，不承诺所有 A 卡可用 |
| P2 | macOS Apple Silicon | 官方 MPS 路径及 CPU 退路，验证匹配权重的推理 | 有上游安装路径，尚未本项目实测 |
| 后续评估 | Intel Mac / CPU-only | 依赖与 CPU 推理可行性 | 不默认纳入首版支持 |

### Windows + NVIDIA

先以当前开发机完成配音闭环，再记录经过验证的 OS、驱动、Python、PyTorch、模型和精度组合。8GB 是本机条件，不作为所有权重的最低显存保证。Windows 11 与不同显卡需分别记录实测状态。

### Windows + AMD

[AMD 的 Windows PyTorch 文档](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html) 提供硬件、系统与框架支持矩阵；部分已发布组合要求 Windows 11、指定 GPU 和 Python 版本。调查时重新确认当前矩阵及版本页，不沿用过期白名单，也不强制所有后端使用 Python 3.10。

GPT-SoVITS 当前 [Windows 安装说明](https://github.com/RVC-Boss/GPT-SoVITS#installation) 列出 CUDA/CPU，ROCm 列在 Linux 安装路径中。因此“AMD 提供 PyTorch”不等于“GPT-SoVITS 已支持 Windows AMD”。需检查第三方依赖、设备判断、精度和完整生成结果。

先评估原生 Windows 官方框架路径；如果不可用，再单独讨论 WSL2/ROCm 等路径的设备兼容及安装成本。WSL2 是可选方案，不等同于原生支持，不自动启用。DirectML、ZLUDA 仅在有明确收益时另行评估，不作为默认安装手段。

检测到 AMD 而没有经过验证的后端时，明确返回实验性或未支持状态；CPU 回退需说明实际速度限制，不静默让用户等待。

### Mac

GPT-SoVITS 官方提供 MPS/CPU 安装选项并列有 Apple Silicon 测试环境；同时注明 Mac GPU 训练质量问题，不能把该训练限制误读为所有推理不可用。

本项目仅评估 Apple Silicon 上的参考音频克隆推理，检查算子、权重、内存、精度、速度和音质；必要时使用 CPU。训练不属于本插件范围，不安排训练兼容性验证。Intel Mac 单列，不共享 Apple Silicon 的支持结论。

## 安装器与验收要求

- `doctor` 返回 OS/架构、显卡、可用后端、驱动、内存和磁盘，并区分已验证、实验性及未支持。
- Agent 适配与硬件后端解耦，同一 skill 使用相同 CLI，根据检测结果选择已验证安装配置。
- 每种后端固定自己的依赖组合和运行时版本，插件的轻量引导不提前依赖 CUDA 包。
- 无对应测试设备时保持待验证状态，不用 mock 结果替代硬件兼容结论。
- 每个宣布支持的 Agent 至少完成 skill 发现、参数传递、产物返回、含空格/中文路径检查；每个宣布支持的硬件配置完成干净环境初始化、短句和长稿生成、重启复用及性能记录。
- 不要求在首版测试所有 Agent 与所有硬件的笛卡尔积，但分别记录实际验证组合，未组合验证的场景明确说明。

## 实施顺序

先完成多 Agent 共享包结构设计与 Windows NVIDIA 闭环，并分别验证三类 Agent 的入口；然后建立 Windows AMD 的可行性报告，最后建立 Mac 的可行性报告。后两者通过实机验证再升级为正式支持，不阻塞 NVIDIA 首版交付。
