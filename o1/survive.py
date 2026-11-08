from __future__ import annotations

from typing import Callable

from .types import Program


ScoreFn = Callable[[Program], float]


def survive_topk(population: list[Program], child: Program, k: int, score_fn: ScoreFn) -> list[Program]:
    """Keep top-k by official score; always include child in the competition."""
    pool = list(population) + [child]
    # unique by version, keep last occurrence
    by_ver: dict[str, Program] = {}
    for p in pool:
        by_ver[p.version] = p
    ranked = sorted(by_ver.values(), key=score_fn, reverse=True)
    return ranked[: max(1, k)]
