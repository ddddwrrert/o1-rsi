from __future__ import annotations

import random
from typing import Sequence

from .types import Program


def _clamp(xs: list[float], lo: float = -2.0, hi: float = 2.0) -> tuple[float, ...]:
    return tuple(min(hi, max(lo, x)) for x in xs)


def apply_arm(
    parent: Program,
    arm_id: str,
    rng: random.Random,
    *,
    version: str,
    island_id: str,
    peers: Sequence[Program] | None = None,
) -> Program:
    """Toy operators on weight vectors — stand-ins for code-edit families."""
    w = list(parent.weights)
    dim = len(w)

    if arm_id == "repair":
        # small corrective noise
        for i in range(dim):
            w[i] += rng.uniform(-0.05, 0.05)
    elif arm_id == "neighborhood":
        i = rng.randrange(dim)
        w[i] += rng.uniform(-0.2, 0.2)
    elif arm_id == "skeleton":
        # re-roll a contiguous block
        if dim >= 2:
            a = rng.randrange(dim - 1)
            b = rng.randrange(a + 1, dim)
            for i in range(a, b + 1):
                w[i] = rng.uniform(-0.8, 0.8)
        else:
            w[0] = rng.uniform(-0.8, 0.8)
    elif arm_id == "restart":
        w = [rng.uniform(-0.8, 0.8) for _ in range(dim)]
    elif arm_id == "speed":
        # aggressive single-coordinate jump
        i = rng.randrange(dim)
        w[i] += rng.choice([-1.0, 1.0]) * rng.uniform(0.3, 0.6)
    elif arm_id == "depth":
        for i in range(dim):
            w[i] += rng.gauss(0.0, 0.08)
    elif arm_id == "crossover":
        peers = [p for p in (peers or []) if p.version != parent.version]
        if peers:
            other = rng.choice(peers)
            mask = [rng.random() < 0.5 for _ in range(dim)]
            w = [other.weights[i] if mask[i] else w[i] for i in range(dim)]
        else:
            for i in range(dim):
                w[i] += rng.uniform(-0.1, 0.1)
    else:
        raise ValueError(f"unknown arm {arm_id}")

    return Program(
        weights=_clamp(w),
        version=version,
        parent_version=parent.version,
        island_id=island_id,
        arm_id=arm_id,
    )
