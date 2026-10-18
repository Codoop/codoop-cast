"""Local report validation/export; research and evidence assessment belong to the agent."""
from datetime import date, datetime
import hashlib
from pathlib import Path
import shutil
from urllib.parse import urlparse

from jsonschema import Draft202012Validator

from .common import read_json, write_json
from .contracts import SCHEMAS, local_resource, require


def validate_report(report_file):
    path = Path(report_file).resolve()
    report = read_json(path)
    Draft202012Validator(read_json(SCHEMAS / 'report.schema.json')).validate(report)
    data = report['data']
    date.fromisoformat(data['as_of'])

    def unique(items):
        result = {item['id']: item for item in items}
        require(len(result) == len(items), 'Duplicate research object ID')
        return result

    sources = unique(data['sources'])
    evidence = unique(data['evidence'])
    claims = unique(data['claims'])
    unique(data['sections']); unique(data['unknowns']); unique(data['conflicts'])
    for source in sources.values():
        datetime.fromisoformat(source['accessed_at'].replace('Z', '+00:00'))
        if source['published_at']:
            date.fromisoformat(source['published_at'])
        if source['url']:
            url = urlparse(source['url'])
            require(url.scheme in ('http', 'https') and bool(url.netloc), 'Invalid source URL')
        require(source['source_type'] != 'webpage' or bool(source['url']), 'Web source needs a URL')
        require(bool(source['snapshot_path']) == bool(source['snapshot_sha256']), 'Snapshot needs both path and SHA-256')
        if source['snapshot_path']:
            snapshot = local_resource(path.parent, source['snapshot_path'])
            require(hashlib.sha256(snapshot.read_bytes()).hexdigest() == source['snapshot_sha256'], 'Source snapshot hash mismatch')
        if source['read_status'] in ('full', 'excerpt'):
            require(bool(source['snapshot_path']), 'Read source needs a retained local evidence snapshot')
        else:
            require(bool(source['notes'].strip()), 'Unread source needs an explanation')
    for item in evidence.values():
        require(item['source_id'] in sources, 'Unknown evidence source')
        require(sources[item['source_id']]['read_status'] in ('full', 'excerpt'), 'Unread source cannot support evidence')
    unsupported = []
    for claim in claims.values():
        require(len(claim['evidence_ids']) == len(set(claim['evidence_ids'])), 'Duplicate claim evidence')
        require(all(eid in evidence for eid in claim['evidence_ids']), 'Unknown claim evidence')
        if not claim['evidence_ids']:
            unsupported.append(claim['id'])
            require(bool(claim['limitations']), 'Unsupported claim needs an explicit limitation')
    paragraphs = [data['summary']] + [p for section in data['sections'] for p in section['paragraphs']]
    for paragraph in paragraphs:
        require(all(cid in claims for cid in paragraph['claim_ids']), 'Unknown paragraph claim')
    for conflict in data['conflicts']:
        require(len(set(conflict['claim_ids'])) >= 2 and all(cid in claims for cid in conflict['claim_ids']), 'Conflict needs at least two existing claims')
    if data['state'] == 'ready':
        require(bool(claims) and not unsupported, 'Ready report requires supported claims')
        require(all(p['claim_ids'] for p in paragraphs), 'Ready report paragraphs need claim references')
    require(not unsupported or data['state'] == 'partial', 'Evidence gaps require partial state')
    warnings = ['This checks structure and retained evidence, not factual truth or source independence.']
    if unsupported:
        warnings.append('Unsupported claims: ' + ', '.join(unsupported))
    return dict(status='ready', report_state=data['state'], claims=len(claims), sources=len(sources),
                unsupported_claim_ids=unsupported, review_required=True, warnings=warnings)


def render_report(report, directory=None):
    data = report['data']
    from .locale import labels
    t = labels(data.get('language', 'zh'), directory)
    claims = {c['id']: c for c in data['claims']}
    evidence = {e['id']: e for e in data['evidence']}
    sources = {s['id']: s for s in data['sources']}

    def paragraph(item):
        source_ids = dict.fromkeys(evidence[eid]['source_id'] for cid in item['claim_ids']
                                   for eid in claims[cid]['evidence_ids'])
        citations = []
        for sid in source_ids:
            source = sources[sid]
            title = source['title'].replace('[', '\\[').replace(']', '\\]')
            target = source['url'] or source['snapshot_path']
            citations.append(f'[{title}](<{target}>)' if target else title)
        return item['text'] + (' ' + ('、' if data.get('language', 'zh').startswith('zh') else ', ').join(citations) if citations else '')

    lines = ['# ' + data['topic'], f'{t("As of")}: {data["as_of"]} · {t("Audience")}: {data["audience"]}',
             t('Scope') + ': ' + data['scope_summary']]
    if data['state'] == 'partial':
        lines.append(t('This report is incomplete; evidence gaps are listed below. Not all conclusions are verified.'))
    lines.append(paragraph(data['summary']))
    for section in data['sections']:
        lines.append('## ' + section['title'])
        lines.extend(paragraph(p) for p in section['paragraphs'])
    caveats = list(dict.fromkeys(note for c in data['claims'] for note in c['limitations']))
    if caveats:
        lines.extend(['## ' + t('Limitations'), '\n'.join('- ' + text for text in caveats)])
    if data['conflicts']:
        lines.extend(['## ' + t('Conflicting sources'), '\n'.join('- ' + c['description'] for c in data['conflicts'])])
    if data['unknowns']:
        lines.extend(['## ' + t('Open questions'), '\n'.join('- ' + u['question'] + ' ' + u['impact'] for u in data['unknowns'])])
    lines.append('## ' + t('Sources and access'))
    for source in sources.values():
        target = source['url'] or source['snapshot_path'] or t('Not retained')
        read_status = {'full':t('Full text read'),'excerpt':t('Relevant excerpt read'),'metadata':t('Metadata only'),'unavailable':t('Unavailable')}[source['read_status']]
        sep = '；' if data.get('language', 'zh').startswith('zh') else '; '
        colon = '：' if data.get('language', 'zh').startswith('zh') else ': '
        lines.append(f'- {source["title"]}{sep}{read_status}{sep}{t("Accessed")}{colon}{source["accessed_at"][:10]}{sep}{t("Published")}{colon}{source["published_at"] or t("Unknown")}{sep}{target}'
                     + (sep + source['notes'] if source['notes'] else ''))
    return '\n\n'.join(lines) + '\n'


def export_report(report_file, output):
    source = Path(report_file).resolve()
    output = Path(output).resolve()
    require(not output.exists(), 'Use a new report output directory')
    checks = validate_report(source)
    report = read_json(source)
    reserved = {'report.json', 'report.md', 'checks.json'}
    snapshots = {}
    for item in report['data']['sources']:
        if item['snapshot_path']:
            relative = item['snapshot_path']
            require(Path(relative).parts[0].lower() not in reserved, 'Snapshot path collides with exported report files')
            snapshots[relative] = local_resource(source.parent, relative)
    markdown = render_report(report, output.parent)
    output.mkdir(parents=True)
    for relative, path in snapshots.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    write_json(output / 'report.json', report)
    (output / 'report.md').write_text(markdown, encoding='utf-8')
    write_json(output / 'checks.json', checks)
    return dict(**checks, package=str(output), report=str(output / 'report.md'),
                handoff=str(output / 'report.json'))
