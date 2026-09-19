"""Run a bounded configured PAPER worker cycle, or serve continuously."""
import argparse
import os
from workers.heartbeat import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--continuous", action="store_true")
    args = parser.parse_args()
    os.environ["PAPER_LOOP_CONFIG"] = args.config
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    run(cycles=None if args.continuous else 1)


if __name__ == "__main__":
    main()
