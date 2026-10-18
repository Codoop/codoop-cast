# Artifact language

All skill instructions and agent metadata are maintained in English. This does not determine the conversation language or the language of deliverables.

Before authoring artifacts, run `config show --directory <content-project-or-batch>` through the shared runtime. Precedence: an explicit current-task language, the nearest ancestor `.codoop-cast/config.json`, the private data-root `config.json`, legacy `cast-project.json` defaults, then `auto`. An explicit task request wins without changing saved defaults. Read this policy even when using an individual skill outside a production workflow.

During setup, reuse saved preferences. For first initialization, offer the current conversation language as the default and save the chosen BCP 47 tag with `setup --output-language <tag>`. Add `--directory <project-or-collection>` for a local override. Without `--feature`, this only saves settings and downloads no feature dependencies. Preserve unrelated settings. Do not create a content project in the plugin source or installation directory.

`auto` means the agent resolves the language from the current explicit request, then the supplied content, then the conversation. Record a concrete tag in new report/script `data.language`. Never write `auto` in a content artifact. When needed pass `--language <tag>` to research/script validation and export, storyboard prepare for plain text, speech generate, external-audio subtitles generate, batch report, and produce plan. For a production run, pass the resolved tag to produce plan and carry that same task override to all downstream skills. Do not infer output language from the English skill text or from a web source's language.

Apply the selected language to report prose, narration, scene text, visual labels, editorial notes, captions and image-generation prompts for readable text. Translate meaning rather than merely changing metadata. Preserve source quotations, proper names, exact numbers, URLs, evidence snapshots, IDs, ASCII paths and schema keys. Research may use sources in other languages. Derive subtitles from the actual display script and aligned speech; do not translate existing audio or captions independently.

Existing artifacts retain their language. When the target changes, create translated revisions and rebuild affected downstream versions; retain approved earlier versions. Structured speech uses the pinned script language, and subtitles from a speech job use that job's language. Changing configuration does not change a reference speaker's language or upload audio. Reference recording language is a separate `voice create --language` setting.

Built-in report/script/batch wrapper labels support Simplified Chinese and English. For another language, first translate every English label key in `<plugin-root>/runtime/codoop-cast/castlib/locale.py` into a string dictionary at `<content-scope>/.codoop-cast/locales/<tag>.json`; keep formatting placeholders unchanged. The runtime reports missing/incomplete locales rather than silently using Chinese. These are editorial labels, not model resources. The host agent can write content in other languages, but the currently integrated voice/alignment routing supports only `zh` and `en`; actual English voice quality still needs listening review. Explain a concrete backend limitation if requested, without changing the user's target language.

Example local configuration:

```json
{
  "schema_version": 1,
  "output_language": "zh-CN"
}
```

This shared file is extensible for future skill settings. Do not introduce a second per-skill language preference.
