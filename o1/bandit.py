from __future__ import annotations

import math
import random
from typing import Mapping

from .types import ArmStat


def ucb1_select(
    menu: tuple[str, ...],
    stats: Mapping[str, ArmStat],
    rng: random.Random,
    *,
    c: float = 1.414,
) -> str:
    """
    UCB1 over the island arm menu.
    Unpulled arms are forced first (cold start), shuffled for fairness.
    """
    if not menu:
        raise ValueError("empty menu")

    unpulled = [a for a in menu if stats.get(a, ArmStat(a)).pulls <= 0]
    if unpulled:
        return rng.choice(unpulled)

    total_pulls = sum(stats[a].pulls for a in menu if a in stats)
    total_pulls = max(total_pulls, 1)
    best_arm = menu[0]
    best_score = float("-inf")
    # slight jitter to break ties
    for arm in menu:
        st = stats[arm]
        exploit = st.mean_reward
        explore = c * math.sqrt(math.log(total_pulls + 1) / st.pulls)
        score = exploit + explore + rng.random() * 1e-9
        if score > best_score:
            best_score = score
            best_arm = arm
    return best_arm


def update_arm(
    stats: dict[str, ArmStat],
    arm_id: str,
    reward: float,
    cost: float = 1.0,
) -> None:
    st = stats.setdefault(arm_id, ArmStat(arm_id=arm_id))
    st.pulls += 1
    # cost-aware reward: Δ / cost
    st.total_reward += reward / max(cost, 1e-9)
    st.total_cost += cost
