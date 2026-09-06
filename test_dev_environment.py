import importlib.util
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
        with patch.object(diagnostic.urllib.request, 'build_opener', side_effect=OSError):
            self.assertEqual(diagnostic.ollama_status()[0], 'UNAVAILABLE (optional)')

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
