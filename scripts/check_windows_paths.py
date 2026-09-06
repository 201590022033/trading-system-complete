"""Check tracked repository paths for Windows-incompatible names."""
from __future__ import annotations

from pathlib import Path
import argparse
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _path_issues(path: str) -> list[str]:
    issues: list[str] = []
    if ':' in path:
        issues.append('colon')
    if '\\' in path:
        issues.append('backslash')
    if '"' in path:
        issues.append('quote')
    if re.search(r'(^|/|["\'])[A-Za-z]:', path):
        issues.append('drive-letter')
    if any(ch in path for ch in '<>|?*'):
        if '<' in path or '>' in path:
            issues.append('angle-bracket')
        if '|' in path:
            issues.append('pipe')
        if '?' in path:
            issues.append('question-mark')
        if '*' in path:
            issues.append('asterisk')
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in path):
        issues.append('control-char')
    for part in path.split('/'):
        if not part:
            continue
        if part != part.rstrip(' .'):
            issues.append('trailing-space-or-dot')
            break
        base = part.rstrip(' .').split('.', 1)[0]
        if re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', base, re.I):
            issues.append('reserved-name')
            break
    return issues


def _git_paths(include_untracked: bool = False) -> list[tuple[str, str]]:
    paths: list[tuple[str, str]] = []
    tracked = subprocess.run(
        ['git', '-C', str(ROOT), 'ls-files', '-z'],
        check=True,
        capture_output=True,
    ).stdout.decode('utf-8', 'surrogateescape').split('\0')
    for path in tracked:
        if path:
            paths.append(('tracked', path))
    if include_untracked:
        untracked = subprocess.run(
            ['git', '-C', str(ROOT), 'ls-files', '--others', '--exclude-standard', '-z'],
            check=True,
            capture_output=True,
        ).stdout.decode('utf-8', 'surrogateescape').split('\0')
        for path in untracked:
            if path:
                paths.append(('untracked', path))
    return paths


def invalid_paths(include_untracked: bool = False) -> list[tuple[str, str, list[str]]]:
    invalid = []
    for source, path in _git_paths(include_untracked=include_untracked):
        issues = _path_issues(path)
        if issues:
            invalid.append((source, path, issues))
    return invalid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--all-files',
        action='store_true',
        help='Also inspect untracked files in the current working tree.',
    )
    args = parser.parse_args()
    invalid = invalid_paths(include_untracked=args.all_files)
    if invalid:
        print('FAIL: Windows-incompatible paths found')
        for source, path, issues in invalid:
            print(f'  {source}\\t{",".join(issues)}\\t{path}')
        return 1
    print('PASS: no Windows-incompatible tracked paths found')
    return 0


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    raise SystemExit(main())
