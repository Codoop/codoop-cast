"""Validate and export agent-authored narration with pinned report provenance."""
import math
from pathlib import Path
import shutil
import unicodedata

from .common import digest, read_json, write_json
from .contracts import local_resource, require, validate_artifact
from .research import validate_report


def load_source(path):
    path = Path(path).resolve()
    if path.suffix.lower() == '.json':
        report = read_json(path)
        require(report.get('kind') == 'report', 'JSON input must be a report artifact; use UTF-8 .md/.txt for an external report.')
        checks = validate_report(path)
        return dict(kind='report', artifact_id=report['artifact_id'], revision=report['revision']), report, checks
    require(path.suffix.lower() in ('.md', '.txt'), 'External reports must be local UTF-8 .md or .txt files.')
    require(bool(path.read_text(encoding='utf-8-sig').strip()), 'External report is empty.')
    return dict(kind='external', sha256=digest(path)), None, None


def validate_script(script_file, source_file=None, target_seconds=None, characters_per_second=4.0):
    path = Path(script_file).resolve()
    artifact = read_json(path)
    require(artifact.get('kind') == 'script', 'Expected a script artifact.')
    validate_artifact(artifact)
    sidecar = None
    if source_file is None:
        sidecar = read_json(path.parent / 'script-source.json')
        require(sidecar['script'] == {k: artifact[k] for k in ('artifact_id', 'revision')}
                and sidecar['script_sha256'] == digest(path), 'Script differs from its exported source record.')
        source_file = local_resource(path.parent, sidecar['source_path'])
        require(digest(source_file) == sidecar['source_sha256'], 'Retained report changed.')
    source_file = Path(source_file).resolve()
    identity, report, report_checks = load_source(source_file)
    require(artifact['data'].get('source') == identity, 'Script source identity/hash is missing or stale.')
    paragraphs = artifact['data']['paragraphs']
    require(bool(paragraphs), 'Narration must contain at least one paragraph.')
    require(len({p['id'] for p in paragraphs}) == len(paragraphs), 'Duplicate paragraph ID.')
    claims = {c['id']: c for c in report['data']['claims']} if report else {}
    used = set()
    for paragraph in paragraphs:
        require(bool(paragraph['display_text'].strip()) and bool(paragraph['spoken_text'].strip()), 'Narration paragraph is empty.')
        require(len(set(paragraph['claim_ids'])) == len(paragraph['claim_ids']), 'Duplicate paragraph claim.')
        if report:
            require(bool(paragraph['claim_ids']) and all(cid in claims for cid in paragraph['claim_ids']), 'Each report-based paragraph needs valid claim references.')
        else:
            require(not paragraph['claim_ids'], 'External report without claim metadata must not invent claim IDs.')
        used.update(paragraph['claim_ids'])
        if paragraph.get('pronunciation_spans'):
            from .script_audio import paragraph_mapping
            paragraph_mapping(paragraph)
    require(isinstance(characters_per_second, (int, float)) and math.isfinite(characters_per_second)
            and characters_per_second > 0, 'Estimate rate must be positive and finite.')
    if target_seconds is not None:
        require(math.isfinite(target_seconds) and target_seconds > 0, 'Target seconds must be positive and finite.')
    count = sum(unicodedata.category(ch)[0] in ('L', 'N') for p in paragraphs for ch in p['spoken_text'])
    estimate = round(count / characters_per_second, 1)
    warnings = []
    if not report:
        warnings.append('External report facts have not been independently verified.')
    elif report_checks['report_state'] == 'partial':
        warnings.append('Source report is partial; preserve its unresolved evidence gaps.')
    for cid in sorted(used):
        claim = claims[cid]
        if claim['kind'] != 'fact' or not claim['evidence_ids'] or claim['limitations']:
            warnings.append('Retain the qualifications of ' + cid + '.')
    return dict(status='ready', paragraphs=len(paragraphs), source=identity, used_claim_ids=sorted(used),
                source_state=report_checks['report_state'] if report else 'unverified',
                duration=dict(estimated=True, spoken_letter_number_count=count, characters_per_second=characters_per_second,
                              estimated_seconds=estimate, target_seconds=target_seconds,
                              method='Unicode letters/numbers divided by assumed rate; punctuation, pauses and pronunciation are not modeled.'),
                review_required=True, warnings=warnings,
                limitation='Checks verify structure and provenance, not factual fidelity, writing quality or actual speaking duration.')


def export_script(script_file, source_file, output, target_seconds=None, characters_per_second=4.0):
    source = Path(source_file).resolve()
    output = Path(output).resolve()
    require(not output.exists(), 'Use a new script output directory.')
    checks = validate_script(script_file, source, target_seconds, characters_per_second)
    artifact = read_json(script_file)
    report = read_json(source) if checks['source']['kind'] == 'report' else None
    files = {}
    if report:
        files['inputs/report.json'] = source
        for item in report['data']['sources']:
            if item['snapshot_path']:
                relative = item['snapshot_path']
                require(Path(relative).parts[0].lower() != 'report.json', 'Report snapshot collides with report.json.')
                files['inputs/' + relative] = local_resource(source.parent, relative)
        retained = 'inputs/report.json'
    else:
        retained = 'inputs/source' + source.suffix.lower()
        files[retained] = source
    from .locale import labels
    t = labels(artifact['data']['language'], output.parent)
    output.mkdir(parents=True)
    for name, original in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
    write_json(output / 'script.json', artifact)
    paragraphs = artifact['data']['paragraphs']
    display = '\n\n'.join(p['display_text'] for p in paragraphs) + '\n'
    spoken = '\n\n'.join(p['spoken_text'] for p in paragraphs) + '\n'
    (output / 'script.txt').write_text(display, encoding='utf-8')
    (output / 'spoken.txt').write_text(spoken, encoding='utf-8')
    note = t('Estimated length: {seconds} seconds at an assumed rate; the actual duration depends on synthesized audio.').format(seconds=checks['duration']['estimated_seconds'])
    if target_seconds is not None:
        note += ' ' + t('Target duration: {seconds} seconds.').format(seconds=f'{target_seconds:g}')
    if not report:
        note += ' ' + t('External source; facts have not been independently verified.')
    elif checks['source_state'] == 'partial':
        note += ' ' + t('The source report is incomplete and has evidence gaps.')
    (output / 'script.md').write_text('# ' + t('Narration script') + '\n\n' + display + '\n---\n\n' + note + '\n', encoding='utf-8')
    write_json(output / 'script-source.json', dict(schema_version='0.1.0',
               script={k: artifact[k] for k in ('artifact_id', 'revision')}, script_sha256=digest(output / 'script.json'),
               source_path=retained, source_sha256=digest(output / retained)))
    write_json(output / 'checks.json', checks)
    return dict(**checks, package=str(output), script=str(output / 'script.md'), handoff=str(output / 'script.json'))
