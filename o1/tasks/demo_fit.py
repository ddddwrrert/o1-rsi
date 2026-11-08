from __future__ import annotations

import math
import random
from dataclasses import dataclass

from ..judge import OfficialJudge
from ..types import Program, Split


@dataclass(frozen=True)
class DemoTask:
    name: str
    dim: int
    targets: dict[str, tuple[float, ...]]
    split: Split
    judge: OfficialJudge
    global_target: tuple[float, ...]


def _score(program: Program, seed_id: str, targets: dict[str, tuple[float, ...]]) -> float:
    tgt = targets[seed_id]
    s = 0.0
    for a, b in zip(program.weights, tgt):
        d = a - b
        s += d * d
    return math.exp(-s)


def build_demo_task(
    seed: int = 0,
    n_public: int = 12,
    n_gate: int = 6,
    n_sealed: int = 6,
) -> DemoTask:
    rng = random.Random(seed)
    dim = 4
    global_target = tuple(rng.uniform(-0.8, 0.8) for _ in range(dim))
    targets: dict[str, tuple[float, ...]] = {}

    def make_ids(prefix: str, n: int) -> list[str]:
        ids = []
        for i in range(n):
            sid = f"{prefix}{i:02d}"
            noise = tuple(rng.uniform(-0.25, 0.25) for _ in range(dim))
            targets[sid] = tuple(global_target[j] + noise[j] for j in range(dim))
            ids.append(sid)
        return ids

    public = tuple(make_ids("pub", n_public))
    gate = tuple(make_ids("gate", n_gate))
    sealed = tuple(make_ids("seal", n_sealed))
    frozen = dict(targets)

    def score_fn(program: Program, seed_id: str) -> float:
        return _score(program, seed_id, frozen)

    all_seeds = public + gate + sealed
    judge = OfficialJudge(score_fn=score_fn, seed_ids=all_seeds)
    return DemoTask(
        name="demo_fit",
        dim=dim,
        targets=frozen,
        split=Split(public=public, gate=gate, sealed=sealed),
        judge=judge,
        global_target=global_target,
    )


def init_program(dim: int, version: str = "c000000", island_id: str | None = None) -> Program:
    # weak start near zero
    return Program(weights=tuple(0.0 for _ in range(dim)), version=version, island_id=island_id)
