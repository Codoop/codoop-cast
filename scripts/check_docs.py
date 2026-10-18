"""Check paired documentation and repository-local Markdown links."""
import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    root = Path(root)
    errors = []
    editions = {lang:{p.relative_to(root/'docs'/lang).as_posix() for p in (root/'docs'/lang).rglob('*.md')} for lang in ('en', 'zh-cn')}
    for lang, other in (('en', 'zh-cn'), ('zh-cn', 'en')):
        for path in sorted(editions[lang] - editions[other]):
            errors.append('Missing ' + other + ' counterpart: ' + path)
    pairs = [('README.md', 'README.zh-cn.md'), ('THIRD_PARTY.md', 'THIRD_PARTY.zh-cn.md'),
             ('docs/README.md', 'docs/README.zh-cn.md'), ('examples/README.md', 'examples/README.zh-cn.md'),
             ('examples/72-second-workflow/README.md', 'examples/72-second-workflow/README.zh-cn.md'),
             ('examples/research-subtitle-timing/report.md', 'examples/research-subtitle-timing/report.en.md'),
             ('examples/script-subtitle-timing/script.md', 'examples/script-subtitle-timing/script.en.md'),
             ('examples/research-subtitle-timing/sources/mdn-webvtt.md', 'examples/research-subtitle-timing/sources/mdn-webvtt.en.md')]
    for pair in pairs:
        for name in pair:
            if not (root/name).is_file():
                errors.append('Missing edition: ' + name)
    files = [root/'README.md', root/'README.zh-cn.md', root/'THIRD_PARTY.md', root/'THIRD_PARTY.zh-cn.md']
    files += [p for folder in ('docs', 'examples', 'skills') for p in (root/folder).rglob('*.md')]
    links = 0
    for path in files:
        if not path.is_file():
            continue
        text = re.sub(r'^```[^\n]*\n.*?^```[^\n]*$', '', path.read_text(encoding='utf-8'), flags=re.M | re.S)
        for match in re.finditer(r'!?\[[^\]]*\]\(([^\n)]+)\)', text):
            value = match[1].strip()
            if value.startswith('<'):
                value = value[1:value.index('>')]
            else:
                value = value.split(' "', 1)[0]
            if re.match(r'^(?:[a-zA-Z][\w+.-]*:|#)', value):
                continue
            target = (path.parent/unquote(value.split('#', 1)[0])).resolve()
            links += 1
            if not target.exists():
                errors.append(str(path.relative_to(root)) + ': broken link ' + value)
    return dict(status='failed' if errors else 'ready', documentation_pairs=len(editions['en']) + len(pairs), local_links=links, errors=errors)


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result['errors'] else 0)
