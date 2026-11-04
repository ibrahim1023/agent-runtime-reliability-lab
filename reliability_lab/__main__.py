"""Public commands; offline verification never selects a model provider."""

import argparse
import json
from pathlib import Path

from reliability_lab.offline import verify_offline


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect evidence and execute local receiver contracts.")
    parser.add_argument("command", choices=["verify-offline", "scripted-root-check", "scripted-filesystem-check", "crash-resume-check", "reported-crash-check", "native-retry-check", "run-budget-check", "budget-lifetime-check", "budget-recovery-check"])
    parser.add_argument("--prediction", default="not supplied", help="Optional learner prediction for a new scripted experiment")
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
        report, code = run_crash_resume(root, learner_prediction=args.prediction)
    elif args.command == "reported-crash-check":
        from reliability_lab.reported_crash import run_reported_crash
        report, code = run_reported_crash(root, learner_prediction=args.prediction)
    elif args.command == "native-retry-check":
        from reliability_lab.native_retry import run_native_retry
        report, code = run_native_retry(root, learner_prediction=args.prediction)
    elif args.command == "run-budget-check":
        from reliability_lab.run_budget import run_budget_check
        report, code = run_budget_check(root, learner_prediction=args.prediction)
    elif args.command == "budget-lifetime-check":
        from reliability_lab.budget_lifetime import run_lifetime
        report, code = run_lifetime(root, learner_prediction=args.prediction)
    elif args.command == "budget-recovery-check":
        from reliability_lab.budget_recovery import run_budget_recovery
        report, code = run_budget_recovery(root, learner_prediction=args.prediction)
    else:
        report, code = verify_offline(root)
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
