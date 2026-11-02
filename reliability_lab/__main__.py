"""Public commands; offline verification never selects a model provider."""

import argparse
import json
from pathlib import Path

from reliability_lab.offline import verify_offline


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect evidence and execute local receiver contracts.")
    parser.add_argument("command", choices=["verify-offline"])
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report, code = verify_offline(root)
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
