"""Read-only development diagnostic. Never prints or loads credential values."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENV_NAMES = ('NEWSAPI_KEY', 'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT',
             'OLLAMA_HOST', 'OLLAMA_LOCAL_MODEL', 'OLLAMA_CLOUD_MODEL', 'OLLAMA_API_KEY',
             'MOONSHOT_API_KEY', 'KIMI_API_KEY', 'MOONSHOT_MODEL', 'KIMI_MODEL', 'HOST', 'PORT')


def dependency_status(root=ROOT):
    missing = []
    if not (root / 'requirements.txt').is_file():
        return ['requirements.txt unavailable']
    constraints = root / 'constraints-dev.txt'
    pins = {}
    if constraints.is_file():
        pins = {re.sub(r'[-_.]+', '-', name).lower(): version for line in constraints.read_text(encoding='utf-8').splitlines()
                if '==' in line and not line.startswith('#') for name, version in [line.split('==', 1)]}
    for line in (root / 'requirements.txt').read_text(encoding='utf-8').splitlines():
        name = re.split(r'[<>=!~;\s]', line.strip())[0]
        if not name or name.startswith('#'):
            continue
        try:
            actual = importlib.metadata.version(name)
            expected = pins.get(re.sub(r'[-_.]+', '-', name).lower())
            if expected and actual != expected:
                missing.append(name + ' (version differs from constraints-dev.txt)')
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
    return missing


def compile_sources(root=ROOT):
    paths = sorted(root.glob('*.py')) + sorted((root / 'scripts').glob('*.py'))
    for path in paths:
        compile(path.read_bytes(), str(path), 'exec')
    return len(paths)


def ollama_status():
    # Only inspect the default local service. Never send configured keys or probe private URLs.
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:11434/api/tags', timeout=2) as response:
            data = json.load(response)
        names = {m.get('name') for m in data.get('models', [])}
        return 'AVAILABLE', 'PRESENT' if 'llama3.2:3b' in names else 'MISSING'
    except Exception:
        return 'UNAVAILABLE (optional)', 'UNKNOWN (service unavailable)'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ollama', action='store_true', help='Also probe only the default local Ollama endpoint')
    parser.add_argument('--compile-only', action='store_true')
    args = parser.parse_args()
    if args.compile_only:
        print('COMPILE: PASS', compile_sources(), 'files (no bytecode written)')
        return 0
    checks = {}
    checks['PYTHON'] = sys.version_info[:2] == (3, 12)
    print('PYTHON:', 'PASS' if checks['PYTHON'] else 'FAIL (use tested Python 3.12.x)')
    print('PYTHON VERSION:', sys.version.split()[0])
    missing = dependency_status()
    checks['DEPENDENCIES'] = not missing
    print('DEPENDENCIES:', 'FAIL missing ' + ', '.join(missing) if missing else 'PASS')
    checks['GIT'] = shutil.which('git') is not None
    print('GIT:', 'PASS' if checks['GIT'] else 'FAIL')
    required = ('AGENTS.md', 'requirements.txt', 'constraints-dev.txt', 'app.py',
                'docs/roadmap/CURRENT_MILESTONE.md', 'analysis/results/hr11/baseline.json')
    absent = [name for name in required if not (ROOT / name).is_file()]
    checks['REQUIRED FILES'] = not absent
    print('REQUIRED FILES:', 'PASS' if not absent else 'FAIL ' + ', '.join(absent))
    repository = False
    if checks['GIT']:
        result = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True)
        repository = result.returncode == 0 and result.stdout.strip() == 'true'
    checks['REPOSITORY'] = repository
    print('REPOSITORY:', 'PASS' if repository else 'FAIL')
    print('ENV VARIABLES: none required for offline tests/research; process status only (.env not read)')
    for name in ENV_NAMES:
        print(' ', name + ':', 'SET' if os.environ.get(name) else 'MISSING (optional)')
    print('ENV FILE:', 'PRESENT (not inspected)' if (ROOT / '.env').exists() else 'ABSENT (optional)')
    if args.ollama:
        service, models = ollama_status()
        print('OLLAMA:', service)
        print('OLLAMA MODELS:', models)
    else:
        print('OLLAMA: NOT_REQUIRED for offline work')
    if not args.ollama:
        print('OLLAMA MODELS: NOT_CHECKED; optional --ollama checks default local model')
    excluded = {'test_cloud', 'test_ost_login', 'test_reddit', 'test_sentiment', 'test_llm_sentiment'}
    modules = [p for p in ROOT.glob('test_*.py') if p.stem not in excluded]
    checks['TEST DISCOVERY'] = bool(modules)
    print('TEST DISCOVERY:', 'PASS' if modules else 'FAIL', len(modules), 'safe modules (execution is a separate task)')
    env = dict(os.environ, PYTHON_DOTENV_DISABLED='1', PYTHONDONTWRITEBYTECODE='1')
    try:
        result = subprocess.run([sys.executable, '-B', '-c', 'import hr11_research; import app; assert app.app.test_client().get("/health").status_code == 200'],
                                cwd=ROOT, env=env, capture_output=True, timeout=60)
        checks['PROJECT IMPORT'] = result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        checks['PROJECT IMPORT'] = False
    print('PROJECT IMPORT:', 'PASS' if checks['PROJECT IMPORT'] else 'FAIL (run dependency install; captured output withheld)')
    checkpoint_path = ROOT / 'docs/roadmap/CURRENT_MILESTONE.md'
    checkpoint = checkpoint_path.read_text(encoding='utf-8') if checkpoint_path.is_file() else ''
    summary = next((line.strip('*') for line in checkpoint.splitlines() if line.startswith('**')), 'UNAVAILABLE')
    print('ROADMAP CHECKPOINT:', summary)
    if repository:
        status = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain'], capture_output=True, text=True)
        print('GIT STATUS:', 'DIRTY' if status.stdout else 'CLEAN')
    else:
        print('GIT STATUS: UNAVAILABLE')
    print('RESULT:', 'PASS (offline development)' if all(checks.values()) else 'FAIL')
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    raise SystemExit(main())
