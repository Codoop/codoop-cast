# Third-party resources

[English](THIRD_PARTY.md) | [简体中文](THIRD_PARTY.zh-cn.md)

codoop-cast's original code is licensed under Apache-2.0; this does not relicense dependencies, downloaded models, fonts, source excerpts or user media. The repository distributes adapters, dependency pins and resource manifests, not a bundle of model weights or installed environments.

## Resource inventory

| Resource | Source and version record | Distribution boundary |
| --- | --- | --- |
| GPT-SoVITS source and pretrained voice resources | [Upstream](https://github.com/RVC-Boss/GPT-SoVITS), `runtime/codoop-cast/resources-voice.json` | Downloaded during private setup; source and individual pretrained resources require their own upstream terms |
| Whisper speech-recognition resources | `resources-voice.json` and pinned dependency files in `runtime/codoop-cast/` | Downloaded resources are separate from this project's license |
| Qwen3 forced aligner | [Model repository](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B-hf), `resources-alignment.json` | Pinned model revision, model card and resources are downloaded into shared data |
| uv and private Python | [uv](https://github.com/astral-sh/uv), bootstrap resource manifests | Separate executable/runtime licenses; no system Python redistribution in this repository |
| PyTorch and Python dependencies | `requirements-*.txt`, `constraints-*.txt`, feature setup | Installed into private feature environments; inspect those distributions for their notices |
| Playwright and Chromium | [Playwright](https://github.com/microsoft/playwright), `resources-video.json` | Browser/vendor notices belong to the downloaded distribution |
| FFmpeg | Feature installation and imageio-ffmpeg dependency | The actual downloaded build and its codecs determine applicable terms; do not assume this project's license covers the executable |
| System fonts | Selected output-profile and host environment | Not bundled; users need the relevant font rights or a suitable alternative |
| Humanizer references | [Humanizer](https://github.com/blader/humanizer), [Humanizer-zh](https://github.com/op7418/Humanizer-zh) | Optional links, not bundled skills or required installations |
| Research evidence snapshots | Per-source URLs and metadata in example/project reports | Source-specific content, not original project code; retained examples identify their source |

This inventory is not a completed license audit or a grant of rights to third-party material. Before redistributing weights, executables, fonts or a packaged environment, retain and review the actual pinned distributions' licenses and notices. The Alpha source release does not claim that every upstream resource has the same commercial-use terms.

User reference recordings, saved voices, generated narration and production assets are not included in the source release. Agent-managed project assets record actual origin and known license information; unknown terms must remain unknown rather than be labeled approved.
