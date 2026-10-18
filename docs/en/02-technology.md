# Technology selection

[English](02-technology.md) | [简体中文](../zh-cn/02-technology.md)

Historical status: GPT-SoVITS had been selected but not deployed; other options were candidates. Capability/license notes came from an earlier official-source review. Recheck the chosen version, model cards, weights and dependencies before integration. Local deployment does not establish commercial-use rights or complete offline operation. See [current readiness](29-release-readiness.md) for subsequent implementation.

## Runtime and application structure

| Layer | Proposal | Reason/boundary |
| --- | --- | --- |
| Interaction | Agent skills + local CLI | Open distribution; host manifests require installation tests |
| Local modules | Python functions/classes | Direct model/file operations without HTTP frameworks |
| Project/task metadata | SQLite | Initial single-machine proposal, without a database cluster |
| Large files | Local project directories | Keep audio/assets/video separate from database records |
| Models | Separate engine environments/processes | Avoid PyTorch/CUDA/Transformers conflicts |
| Batch | Initially one worker with durable tasks | Queue GPU work; add infrastructure only for demonstrated throughput needs |

The project does not start HTTP services or listen on ports. Modules call Python directly. GPT-SoVITS can use a reusable subprocess within a task to isolate dependencies, communicating JSON via standard streams and large files via local paths. Diagnostics go to stderr/files, not structured message output.

## Language models and research

- [Ollama](https://github.com/ollama/ollama): candidate local model runner; size depends on hardware measurements.
- [SearXNG](https://github.com/searxng/searxng): candidate self-hosted search; it still contacts external sources and depends on their availability/network.
- [Crawl4AI](https://github.com/unclecode/crawl4ai): candidate extraction tool. Login, anti-bot or failed pages must report failures; allow supplied material.
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher): orchestration reference, not a first-version dependency.

The initial bounded flow was question decomposition → search → extraction → retained evidence → report. Limit retrieval count/time rather than exploring indefinitely.

## Spoken editing

[Humanizer-zh](https://github.com/op7418/Humanizer-zh) and [Humanizer](https://github.com/blader/humanizer) are writing instructions, not independent models. Review licenses, retain provenance/version when integrating, and preserve factual qualifications.

## Local TTS

| Candidate | Use | Decision |
| --- | --- | --- |
| [CosyVoice](https://github.com/QwenAudio/CosyVoice) | Chinese reference voice/narration | Later alternative, not integrated initially |
| [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | Reference voice cloning | Later alternative, not integrated initially |
| [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) | Reference-driven narration | User's first choice; inference only |
| [ChatTTS](https://github.com/2noise/ChatTTS) | Conversational experiments | Not default; public weights have noncommercial restrictions, and reusing random timbre is not cloning a specific person |

The previously reviewed cards for [these CosyVoice 3 weights](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512) and [Qwen3-TTS 0.6B Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) stated Apache-2.0. This does not extend to every resource in those projects.

Compare the same reference and script: similarity, numbers/polyphones, omissions/repeats, continuity, runtime and peak VRAM. Do not promise minimum VRAM or real-time speed before measuring.

## Alignment and recognition

- First alignment candidate: [Qwen3-ForcedAligner](https://github.com/QwenLM/Qwen3-ASR), using real audio and known text.
- Alternative: [WhisperX](https://github.com/m-bain/whisperX), subject to Chinese alignment model/dependency checks.
- Speech quality-check candidates: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) or Qwen3-ASR. Recognition differences inform review/retry; they must not overwrite an accepted script.

## Video rendering

| Approach | Fit | Decision |
| --- | --- | --- |
| [Remotion](https://github.com/remotion-dev/remotion) | Dynamic layouts, diagrams, parameterized templates, previews | Candidate for visual validation; review its [specific license](https://www.remotion.dev/docs/license) before adoption |
| [MoviePy](https://github.com/Zulko/moviepy) + [FFmpeg](https://ffmpeg.org/) | Composition, overlays, simple animation, encoding | Alternative; avoid maintaining two first-version renderers |

Prefer MP4/H.264/AAC and standalone SRT. Aspect/frame rate belong to the production profile. Review the actual FFmpeg build/codec distribution terms.

## Whole-project references

- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo): topic-to-video workflow reference.
- [NarratoAI](https://github.com/linyqh/NarratoAI): existing-video narration/editing reference.

Do not merge entire projects before establishing a need. Identify their external media and online model dependencies individually; do not assume default local-only operation.
