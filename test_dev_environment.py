import importlib.util
import contextlib
import io
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DevelopmentEnvironmentTests(unittest.TestCase):
    def test_diagnostic_reads_repository_documents_as_utf8(self):
        diagnostic = load('check_dev_environment')
        original_read = Path.read_text
        reads = []

        def windows_read(path, *args, **kwargs):
            reads.append(path.name)
            # Emulate Windows' legacy default even on UTF-8 Linux hosts.
            kwargs.setdefault('encoding', 'cp1252')
            return original_read(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs/roadmap').mkdir(parents=True)
            (root / 'requirements.txt').write_bytes('# Unicode: ”\nflask\n'.encode('utf-8'))
            (root / 'constraints-dev.txt').write_bytes('# Unicode: ”\nflask==3.1.3\n'.encode('utf-8'))
            (root / 'docs/roadmap/CURRENT_MILESTONE.md').write_bytes('**Checkpoint ”**\n'.encode('utf-8'))
            with patch.object(Path, 'read_text', windows_read), patch.object(
                diagnostic.importlib.metadata, 'version', return_value='3.1.3'
            ):
                self.assertEqual(diagnostic.dependency_status(root), [])
                output = io.StringIO()
                with patch.object(diagnostic, 'ROOT', root), patch.object(
                    diagnostic, 'dependency_status', return_value=[]
                ), patch.object(diagnostic.sys, 'argv', ['diagnostic']), patch.object(
                    diagnostic.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'true', '')
                ), contextlib.redirect_stdout(output):
                    diagnostic.main()
                self.assertIn('ROADMAP CHECKPOINT: Checkpoint ”', output.getvalue())
            self.assertEqual(set(reads), {'requirements.txt', 'constraints-dev.txt', 'CURRENT_MILESTONE.md'})

    def test_protected_artifacts_survive_windows_and_linux_checkout(self):
        baseline = json.loads((ROOT / 'analysis/results/hr11/baseline.json').read_text(encoding='utf-8'))
        paths = sorted(set(baseline['immutable_sha256']) | set(subprocess.check_output(
            ['git', 'ls-files', 'analysis/data', 'analysis/results'], cwd=ROOT
        ).decode('utf-8').splitlines()))
        # A separate index exercises real checkout conversion without touching this worktree.
        import os
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            (temp / 'objects').mkdir()
            objects = subprocess.check_output(
                ['git', 'rev-parse', '--git-path', 'objects'], cwd=ROOT
            ).decode('utf-8').strip()
            env = dict(os.environ, GIT_INDEX_FILE=str(temp / 'index'),
                       GIT_OBJECT_DIRECTORY=str(temp / 'objects'),
                       GIT_ALTERNATE_OBJECT_DIRECTORIES=str((ROOT / objects).resolve()))
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=ROOT, env=env)
            git('read-tree', 'HEAD')
            git('add', '--', '.gitattributes')
            for autocrlf, eol in [('true', 'crlf'), ('false', 'lf')]:
                destination = temp / autocrlf
                destination.mkdir()
                git('-c', 'core.autocrlf=' + autocrlf, '-c', 'core.eol=' + eol,
                    'checkout-index', '--force', '--prefix=' + destination.as_posix() + '/', '--', *paths)
                for path in paths:
                    with self.subTest(autocrlf=autocrlf, path=path):
                        self.assertEqual((destination / path).read_bytes(), git('show', 'HEAD:' + path))

    def test_safe_discovery_excludes_all_manual_probes(self):
        runner = load('run_tests')
        names = runner.test_modules()
        self.assertFalse(set(names) & runner.EXCLUDED)
        self.assertIn('test_hr10_robustness', names)
        self.assertIn('test_hr11_regression', runner.test_modules(True))

    def test_missing_requirements_are_reported(self):
        diagnostic = load('check_dev_environment')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(diagnostic.dependency_status(Path(tmp)), ['requirements.txt unavailable'])
            (Path(tmp) / 'requirements.txt').write_text('definitely-missing-project-package==1\n')
            self.assertEqual(diagnostic.dependency_status(Path(tmp)), ['definitely-missing-project-package'])

    def test_ollama_unavailable_is_not_required(self):
        diagnostic = load('check_dev_environment')
        with patch.object(diagnostic.urllib.request, 'build_opener', side_effect=OSError), \
             patch.object(diagnostic, 'ollama_exe_path', return_value=None):
            status = diagnostic.ollama_status()
            self.assertEqual(status['state'], 'NOT_INSTALLED')
            self.assertFalse(status['installed'])
            self.assertFalse(status['reachable'])

    def test_compile_does_not_write_bytecode(self):
        diagnostic = load('check_dev_environment')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'sample.py').write_text('answer = 42\n')
            self.assertEqual(diagnostic.compile_sources(root), 1)
            self.assertFalse((root / '__pycache__').exists())

    def test_diagnostic_detects_dependency_version_drift(self):
        diagnostic = load('check_dev_environment')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'requirements.txt').write_text('flask>=2\n')
            (root / 'constraints-dev.txt').write_text('flask==3.1.3\n')
            with patch.object(diagnostic.importlib.metadata, 'version', return_value='2.0.0'):
                self.assertEqual(diagnostic.dependency_status(root), ['flask (version differs from constraints-dev.txt)'])
