# Why subtitles need a timeline

English reading edition of the Chinese example. The original report.json/report.md and retained source remain canonical; translation does not change their identity/hashes.

As of: 2026-10-17 · Audience: people making their first explanatory narration video.

Scope: use WebVTT cues to explain timing, without comparing aligners or platform posting rules.

Captions need to know when to appear/disappear. In WebVTT each cue contains text plus start/end times. [MDN: WebVTT API](https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API)

## A cue is a timed prompt card

Think of a cue as a card carrying words and start/end times. WebVTT connects text with audiovisual timing through these entries. [MDN: WebVTT API](https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API)

## Why check after changing narration?

If a sentence moves in new audio but its old caption does not, the cue may appear early/late. Therefore recheck timing after replacing speech; identical words do not establish identical timing. This is an inference from the mechanism. [MDN: WebVTT API](https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API)

## Limitations

- This uses WebVTT without verifying every caption format.
- The recheck recommendation is not an alignment-accuracy measurement.

## Open question

- How accurate is an aligner for this audio? No tool benchmark was performed here; listen/view during production.

## Sources and access

- MDN: WebVTT API; relevant definition/Concepts and usage excerpts read on 2026-10-17; publication unknown. Only a short Chinese paraphrase is retained, not a full-page archive: https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API.
