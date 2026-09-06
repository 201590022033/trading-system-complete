"""Run the established offline unittest suite without manual provider probes."""
from pathlib import Path
import argparse
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'test_cloud', 'test_ost_login', 'test_reddit', 'test_sentiment', 'test_llm_sentiment'}


def test_modules(focused=False):
    return [p.stem for p in sorted(ROOT.glob('test_*.py'))
            if p.stem not in EXCLUDED and (not focused or p.stem.startswith('test_hr11_') or p.stem == 'test_dev_environment')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--focused', action='store_true')
    args = parser.parse_args()
    os.chdir(ROOT)
    os.environ['PYTHON_DOTENV_DISABLED'] = '1'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.loadTestsFromNames(test_modules(args.focused))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
