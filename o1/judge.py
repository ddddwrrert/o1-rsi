from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .types import Program


ScoreFn = Callable[[Program, str], float]


@dataclass
class OfficialJudge:
    """Frozen official V: only this path may mint fitness."""

    score_fn: ScoreFn
    seed_ids: tuple[str, ...]

    def score_one(self, program: Program, seed_id: str) -> float:
        if seed_id not in self.seed_ids:
            raise KeyError(f"seed {seed_id} not in judge universe")
        return float(self.score_fn(program, seed_id))

    def mean(self, program: Program, seed_ids: tuple[str, ...] | list[str]) -> float:
        if not seed_ids:
            raise ValueError("empty seed set")
        return sum(self.score_one(program, s) for s in seed_ids) / len(seed_ids)
