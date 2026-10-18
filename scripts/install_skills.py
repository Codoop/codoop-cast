"""Fallback install: keep skills/runtime/scripts adjacent. No global dependencies."""
import argparse
import json
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', choices=['codex', 'claude', 'cursor'], required=True)
    parser.add_argument('--agent-home', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    home = (args.agent_home or Path.home() / ('.' + args.agent)).expanduser().resolve()
    # Use a complete namespaced bundle and point skill discovery at its folders.
    bundle = home / 'codoop-plugins/codoop-cast'
    actions = [{'source': str(source / folder), 'target': str(bundle / folder)} for folder in ('skills', 'runtime', 'scripts', 'schemas', 'LICENSE', 'NOTICE', 'THIRD_PARTY.md', 'THIRD_PARTY.zh-cn.md') if (source / folder).exists()]
    # Reject discovery collisions before copying or upgrading any bundle files.
    discovery = home / 'skills'
    for skill in (source / 'skills').iterdir():
        if not skill.is_dir():
            continue
        target = discovery / skill.name
        expected = bundle / 'skills' / skill.name
        if (target.exists() or target.is_symlink()) and not (target.is_symlink() and target.resolve() == expected.resolve()):
            raise RuntimeError(f'Refusing to overwrite existing skill: {target}')
    if not args.dry_run:
        for action in actions:
            if Path(action['source']).is_dir():
                shutil.copytree(action['source'], action['target'], dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            else:
                Path(action['target']).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(action['source'], action['target'])
        discovery = home / 'skills'
        discovery.mkdir(parents=True, exist_ok=True)
        for skill in (source / 'skills').iterdir():
            if not skill.is_dir():
                continue
            skill = bundle / 'skills' / skill.name
            target = discovery / skill.name
            if target.exists() or target.is_symlink():
                if target.is_symlink() and target.resolve() == skill.resolve():
                    continue
                raise RuntimeError(f'Refusing to overwrite existing skill: {target}')
            try:
                target.symlink_to(skill, target_is_directory=True)
            except OSError as exc:
                raise RuntimeError('Creating discovery links failed. Use native plugin installation or enable Windows Developer Mode for symlinks. The bundle is preserved.') from exc
    print(json.dumps({'status': 'preview' if args.dry_run else 'installed', 'bundle': str(bundle), 'actions': actions}, ensure_ascii=False))


if __name__ == '__main__':
    main()
