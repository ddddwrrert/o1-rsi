from __future__ import annotations

import random

from o1.bandit import ucb1_select, update_arm
from o1.types import ArmStat


def test_ucb1_prefers_unpulled():
    rng = random.Random(0)
    menu = ("repair", "skeleton", "restart")
    stats = {
        "repair": ArmStat("repair", pulls=5, total_reward=1.0),
        "skeleton": ArmStat("skeleton", pulls=5, total_reward=2.0),
        "restart": ArmStat("restart", pulls=0, total_reward=0.0),
    }
    picks = {ucb1_select(menu, stats, rng) for _ in range(5)}
    assert picks == {"restart"}


def test_update_arm_cost_aware():
    stats: dict[str, ArmStat] = {}
    update_arm(stats, "repair", reward=0.2, cost=2.0)
    assert stats["repair"].pulls == 1
    assert abs(stats["repair"].mean_reward - 0.1) < 1e-9
