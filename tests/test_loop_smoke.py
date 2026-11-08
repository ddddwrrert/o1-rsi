from __future__ import annotations

from pathlib import Path

from o1.loop import O1Config, run_o1


def test_run_o1_smoke(tmp_path: Path):
    cfg = O1Config(budget_total=40, seed=1, migrate_every=8, stall_patience=6, policy_trial_len=4, out_dir=str(tmp_path / "run"))
    result = run_o1(cfg)
    assert result.candidates >= 3
    assert result.tip_version
    assert (tmp_path / "run" / "report.json").exists()
    assert (tmp_path / "run" / "events.jsonl").exists()
    assert result.budget["accounts"]["meta"] == 0
    # should make some progress on toy task from zero init
    assert result.tip_public > 0.01
