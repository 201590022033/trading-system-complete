"""CLI: transform a raw ViewPoint HAR into ignored structural evidence."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from viewpoint_discovery import sanitize_har_file

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
args = parser.parse_args()
result = sanitize_har_file(args.input, args.output)
print(f"SANITIZED entries={result['entry_count']}")
