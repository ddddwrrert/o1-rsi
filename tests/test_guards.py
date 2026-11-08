from __future__ import annotations

import json
from pathlib import Path

from o1.loop import O1Config, run_o1
from o1.tasks.demo_fit import build_demo_task
from o1.types import Program


def test_tip_streak_guarantee_force_admit(tmp_path: Path):
    """Public keeps beating tip but gate is hostile → after k rejects, force-admit."""
    task = build_demo_task(seed=0)

    # Monkeypatch gate to always look worse than incumbent, so only streak can promote.
    real_gate = task.judge.mean

    def hostile_mean(program: Program, seed_ids):
        seeds = tuple(seed_ids)
        if seeds == task.split.gate:
            # any non-init program gets a terrible gate
            if program.version == "c000000" or all(abs(x) < 1e-15 for x in program.weights):
                return real_gate(program, seed_ids)
            return -1.0
        return real_gate(program, seed_ids)

    task.judge.mean = hostile_mean  # type: ignore[method-assign]

    cfg = O1Config(
        budget_total=50,
        seed=0,
        migrate_every=100,
        stall_patience=100,
        tip_streak_guarantee=3,
        tip_gate_slack=0.02,
        out_dir=str(tmp_path / "streak"),
    )
    result = run_o1(cfg, task=task)
    assert result.tip_streak_admits >= 1
    assert result.tip_version != "c000000"
    events = (tmp_path / "streak" / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    reasons = [json.loads(line).get("reason") for line in events if json.loads(line).get("phase") == "tip_update"]
    assert any(r and str(r).startswith("streak_guarantee") for r in reasons)


def test_policy_soft_admit_non_worse(tmp_path: Path):
    cfg = O1Config(
        budget_total=80,
        seed=2,
        migrate_every=15,
        stall_patience=3,
        policy_trial_len=3,
        policy_admit_slack=0.05,
        out_dir=str(tmp_path / "soft"),
    )
    result = run_o1(cfg)
    events = [
        json.loads(line)
        for line in (tmp_path / "soft" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    admits = [e for e in events if e.get("phase") == "policy_admit"]
    # With soft slack, trials that start should often non-worse-admit or improve-admit
    if any(e.get("phase") == "policy_trial_start" for e in events):
        assert admits or any(e.get("phase") == "policy_rollback" for e in events)
    assert result.budget["accounts"]["meta"] == 0
