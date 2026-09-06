"""Conservative project venv bootstrap; no system installs, secrets or global changes."""
from pathlib import Path
import argparse
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venv', type=Path, default=ROOT / '.venv')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Use Python 3.12.x; no system Python will be installed.')
    destination = args.venv.resolve()
    if destination.exists() and any(destination.iterdir()) and not (destination / 'pyvenv.cfg').is_file():
        raise SystemExit('Refusing to overwrite a non-venv directory.')
    if not (destination / 'pyvenv.cfg').exists():
        venv.EnvBuilder(with_pip=True).create(destination)
    python = destination / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    subprocess.run([str(python), '-c', 'import sys; assert sys.version_info[:2] == (3,12), "Existing venv is not Python 3.12"'], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt'), '-c', str(ROOT / 'constraints-dev.txt')], check=True)
    subprocess.run([str(python), '-m', 'pip', 'check'], check=True)
    subprocess.run([str(python), str(ROOT / 'scripts/check_dev_environment.py')], check=True)
    print('Setup complete. .env was not created or changed. Select the project .venv interpreter in VS Code.')


if __name__ == '__main__':
    main()
