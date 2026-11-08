from __future__ import annotations

import argparse
import json
from pathlib import Path

from .loop import O1Config, run_o1


def cmd_run(args: argparse.Namespace) -> int:
    cfg = O1Config(
        budget_total=args.budget,
        seed=args.seed,
        migrate_every=args.migrate_every,
        stall_patience=args.stall_patience,
        policy_trial_len=args.policy_trial_len,
        tip_gate_slack=args.tip_gate_slack,
        tip_streak_guarantee=args.tip_streak_guarantee,
        policy_admit_slack=args.policy_admit_slack,
        out_dir=args.out,
    )
    result = run_o1(cfg)
    print(
        json.dumps(
            {
                "framework": "O1",
                "tip_version": result.tip_version,
                "tip_public": result.tip_public,
                "tip_gate": result.tip_gate,
                "tip_sealed": result.tip_sealed,
                "candidates": result.candidates,
                "policy_trials": result.policy_trials,
                "policy_soft_admits": result.policy_soft_admits,
                "tip_streak_admits": result.tip_streak_admits,
                "migrations": result.migrations,
                "out_dir": result.out_dir,
                "budget": result.budget,
            },
            indent=2,
        )
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = Path(args.run)
    report_path = root / "report.json"
    if not report_path.exists():
        raise SystemExit(f"missing {report_path}")
    print(report_path.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="o1", description="O1-RSI: islands × bandit arms")
    sub = p.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run O1 on the demo_fit task")
    run_p.add_argument("--budget", type=int, default=120)
    run_p.add_argument("--seed", type=int, default=0)
    run_p.add_argument("--migrate-every", type=int, default=20)
    run_p.add_argument("--stall-patience", type=int, default=12)
    run_p.add_argument("--policy-trial-len", type=int, default=10)
    run_p.add_argument("--tip-gate-slack", type=float, default=0.02)
    run_p.add_argument("--tip-streak-guarantee", type=int, default=3)
    run_p.add_argument("--policy-admit-slack", type=float, default=0.01)
    run_p.add_argument("--out", type=str, default="runs/o1_demo")
    run_p.set_defaults(func=cmd_run)

    rep_p = sub.add_parser("report", help="print report.json from a run directory")
    rep_p.add_argument("run", type=str)
    rep_p.set_defaults(func=cmd_report)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
