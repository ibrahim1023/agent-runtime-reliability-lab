"""Public commands; offline verification never selects a model provider."""

import argparse
import json
from pathlib import Path

from reliability_lab.offline import verify_offline


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect evidence and execute local receiver contracts.")
    parser.add_argument("command", choices=["verify-offline", "scripted-root-check", "scripted-filesystem-check", "crash-resume-check"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.command == "scripted-root-check":
        from reliability_lab.scripted_root import run_scripted_root
        report, code = run_scripted_root(root)
    elif args.command == "scripted-filesystem-check":
        from reliability_lab.scripted_filesystem import run_scripted_filesystem
        report, code = run_scripted_filesystem(root)
    elif args.command == "crash-resume-check":
        from reliability_lab.crash_resume import run_crash_resume
        report, code = run_crash_resume(root)
    else:
        report, code = verify_offline(root)
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
