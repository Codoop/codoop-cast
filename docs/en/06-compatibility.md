# Agent and hardware compatibility plan

[English](06-compatibility.md) | [简体中文](../zh-cn/06-compatibility.md)

Historical planning/official-source study, before actual installation/inference validation. The user set the order Windows/NVIDIA → Windows/AMD → Mac. See [current readiness](29-release-readiness.md) for later results.

## Agents: following codoop-flow

Use thin host adapters over shared skills/runtime, following [codoop-flow installation](https://github.com/Codoop/codoop-flow/blob/main/docs/install.md) and manifests. The product is not Codex-only.

| Agent | Planned distribution | Required acceptance |
| --- | --- | --- |
| Codex Desktop/CLI | Plugin/marketplace manifests | Install, discover, resolve runtime, execute locally |
| Claude Code | Plugin/marketplace manifests | Install, discover, resolve runtime, execute locally |
| Cursor | Plugin manifest and copy fallback | Load, discover, resolve runtime, execute locally |
| Others | Complete skills/runtime copy if format supported | Test real host; copied files alone do not prove usability |

Record results and host versions separately for the first three; publish commands after package tests. Others are best-effort, without universal compatibility claims.

Proposed structure:

```text
.codex-plugin/plugin.json
.claude-plugin/plugin.json
.cursor-plugin/plugin.json
<host marketplace manifests>
skills/<skill-name>/SKILL.md
runtime/codoop-cast/              # shared CLI/modules/adapters
scripts/                         # installation/packaging
docs/
```

This plan itself did not create files. Keep one runtime, resolved from the installed skill rather than cwd. Complete-copy fallback must preserve relative runtime locations, not copy only SKILL.md.

Borrow distribution ideas, not codoop-flow business restrictions: content folders need not be Git repositories or use ticket directories. Supply Windows-native bootstrap paths; Bash must not be a prerequisite for fallback installation.

## Hardware stages

| Priority | Platform | Path | Status at planning |
| --- | --- | --- | --- |
| P0 | Windows/NVIDIA | CUDA, compatible dependencies, reference speech | RTX 3070 Ti 8GB detected; inference pending |
| P1 | Windows/AMD | Exact GPU/OS/PyTorch support, then complete GPT-SoVITS synthesis | Investigation; not all AMD cards promised |
| P2 | Apple Silicon macOS | MPS/CPU and matching weights | Upstream path exists; project untested |
| Later | Intel Mac / CPU-only | Dependencies and CPU feasibility | Not first-version defaults |

### Windows/NVIDIA

Complete the development-machine speech loop first; record OS, driver, Python, PyTorch, model and precision. 8GB describes this machine, not a minimum for every model. Record Windows 11/other GPUs independently.

### Windows/AMD

[AMD's Windows PyTorch matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html) specifies hardware/OS/framework combinations; some require Windows 11, particular GPUs and Python versions. Recheck current versioned documentation, not stale allowlists; do not force every backend onto Python 3.10.

The reviewed [GPT-SoVITS installation](https://github.com/RVC-Boss/GPT-SoVITS#installation) listed CUDA/CPU for Windows and ROCm under Linux. Available AMD PyTorch does not establish full GPT-SoVITS Windows support. Check third-party dependencies, device branching, precision and actual output.

Investigate the official native path first. If unavailable, discuss WSL2/ROCm compatibility and setup cost separately; WSL2 is optional, not native support, and must not be enabled automatically. Consider DirectML/ZLUDA only for clear benefits, never as default installation workarounds.

Without a validated backend, return experimental/unsupported explicitly. Explain CPU fallback speed rather than leaving users waiting silently.

### Mac

Upstream has MPS/CPU installation and Apple Silicon test environments. Its Mac GPU training-quality warning does not mean all inference is unavailable.

Evaluate reference-driven inference only: operators, weights, memory, precision, speed and quality; use CPU if necessary. Training is outside scope, so no training-compatibility work. Intel Mac is separate and cannot inherit Apple Silicon results.

## Installer acceptance

- Doctor should report OS/architecture, GPU/backend/driver, RAM/disk and verified/experimental/unsupported status.
- Decouple host adapters from hardware; skills use one CLI selecting validated backend profiles.
- Each backend pins its own environment/dependencies; lightweight bootstrap does not initially require CUDA packages.
- Without equipment, retain unverified status; mocks do not establish compatibility.
- Every supported host needs discovery, parameter/output handling and Chinese/space-path tests. Each hardware profile needs clean setup, short/long synthesis, restart/reuse and performance records.
- The first release need not test the full Cartesian product, but must identify actual combinations and untested cross-combinations.

## Sequence

Design the shared multi-agent package, complete Windows/NVIDIA, and test each host entry. Then produce Windows/AMD and Mac feasibility reports, promoting them only after real-device validation. Their work does not block the NVIDIA alpha.
