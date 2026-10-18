# Local execution

Windows launcher (PowerShell; use the absolute path resolved from the skill):

```powershell
& '<plugin-root>/scripts/cast.ps1' doctor --feature voice
```

If host execution policy prevents running a local script, follow host permission rules; do not change machine execution policy. An available Python 3.10+ may call `<plugin-root>/runtime/codoop-cast/cast.py` directly. The PowerShell launcher can bootstrap private Python through pinned uv when Python is absent.

Set `CODOOP_CAST_HOME` in the child environment to choose a data disk. All later commands must use the same root. Default is the platform user data directory. Never hard-code a developer path. Download and model-load progress is in stderr/logs; command runs locally with no HTTP listener.

CLI arguments (arguments following `cast.py` or `cast.ps1`):

```text
doctor --feature voice
setup --feature voice
voice list
voice create --audio <absolute-source-file> [--reference-text <exact-transcript-for-a-short-clip>] [--name <name>] [--language zh|en]
voice confirm --id <draft-voice-id> --reference-text <confirmed-selected-clip-text>
speech generate --text-file <utf8-file> [--voice <name-or-id>] [--output <new-wav-path>]
speech generate --text <script> [--voice <name-or-id>]
task status --job <id>
speech retry --job <id> --segment 2 [--text <corrected-spoken-text>]
speech resume --job <id>
speech export --job <id> [--output <new-wav-path>]
task cancel --job <id>
```

Python entry accepts global `--root <data-directory>` before the subcommand. Prefer passing script files for long text; do not interpolate user text into shell code. Quote paths correctly for the shell or use a subprocess argument list. Output destinations must be new files; existing files are not overwritten.

Generation runs in the foreground; use the host's long-running process support and check progress via `task status`. The job ID appears in the log filename while running and final JSON. Cancellation takes effect between segments. Resume skips valid selected segments; retry creates new attempts without deleting older files. Current retry operates on runtime segment groups, not necessarily each sentence.

Ready means model-load verification passed. `reference_inference_verified` separately records whether a reference-based inference has succeeded on this machine; neither flag proves the user's subjective voice similarity.

## Narration policy and artifacts

New tasks use pretrained v2Pro. Setup manages its matching weights and speaker encoder; users do not select model internals or supply training data. Existing jobs retain their recorded model when resumed or retried.

The runtime preserves original.txt and produces narration.txt separately. Conservative Chinese punctuation hints turn semicolons and selected commas in long sentences into full stops without changing words. Do not promise semantic rewriting or identical rhythm for every script. Do not silently add the wording used in a demonstration.

New scripts are grouped up to 100 characters for generation, with the backend's fragment interval set to 0.15 seconds and no extra export join silence. Legacy jobs without a synthesis policy keep their original fallback intervals. These are internal defaults, not questions the user must answer.

Final JSON artifacts include WAV, its sample-accurate segment manifest, and original/spoken text files. New attempts also record actual backend-normalized text and its display mapping; narration.txt is the text before backend normalization. Unsupported mappings are retained as explicit errors without discarding successful speech. Use the manifest's selected segment texts and real audio for downstream subtitles; fixed pauses and character counts are not word timestamps. A retry with corrected text updates narration.txt while retaining original.txt and previous attempts. Subtitles must be regenerated when selected audio or spoken text changes. Use codoop-subtitles independently after narration; it has its own alignment environment.


## Structured narration

Prefer `speech generate --script-file <script/vNNN/script.json> --voice <voice-id> --output <voice/vNNN/narration.wav>` for project scripts. This preserves the exact script artifact, paragraph IDs, display and spoken forms, and claim references. Plain --text/--text-file remain independent legacy entry points and cannot recover structured provenance that was never provided.

A paragraph may become several synthesis chunks. Each chunk records script_spans in original spoken_text and display_span in original display_text. Captured frontend normalization and its display mapping are separate from these original texts. No generated segment ID is substituted for a paragraph ID. Structured export automatically adds narration.json, script.json, original.txt and narration.txt alongside the WAV; use a new voice version directory. The copied engine manifest still references private chunk files; it is not a fully portable synthesis cache.

For differing display/spoken forms, conservative numeric/punctuation mappings work directly. A true pronunciation substitution requires paragraph.pronunciation_spans with explicit Unicode codepoint half-open display_start/display_end/spoken_start/spoken_end ranges. Agent can construct these from the agreed readout; do not ask users to calculate indices. Ranges must be ordered/nonoverlapping and the surrounding text must map without unrelated rewrites. Treat the entire pronunciation span as a timing group, not fabricated individual character times. No duration limit is imposed on the user's original reference audio by this adapter.

`speech retry --job <id> --segment <n>` can regenerate unchanged structured chunks. --text replacement is rejected for structured jobs because it invalidates the pinned script: revise script.json and create a new task instead. Do not edit a registered project version or silently weaken script linkage to make a retry work.
