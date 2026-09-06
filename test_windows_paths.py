import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WindowsPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load('check_windows_paths')

    def test_repository_has_no_windows_illegal_tracked_paths(self):
        self.assertEqual(self.checker.invalid_paths(), [])

    def test_literal_windows_absolute_path_is_flagged(self):
        bad = '"C:\\Users\\Administrator\\Downloads\\Codex Prompt — Short-Term Multi-Instrument Integration Milestone.md"'
        issues = self.checker._path_issues(bad)
        self.assertIn('colon', issues)
        self.assertIn('backslash', issues)
        self.assertIn('quote', issues)
        self.assertIn('drive-letter', issues)


if __name__ == '__main__':
    unittest.main()
