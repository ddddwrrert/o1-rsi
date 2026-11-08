from __future__ import annotations

import math
import random
from typing import Callable

from .types import Program


ScoreFn = Callable[[Program], float]


def select_parent(
    population: list[Program],
    style: str,
    score_fn: ScoreFn,
    rng: random.Random,
    *,
    parent_pulls: dict[str, int] | None = None,
) -> Program:
    if not population:
        raise ValueError("empty population")
    if len(population) == 1:
        return population[0]

    if style == "fitness":
        scores = [max(score_fn(p), 1e-12) for p in population]
        total = sum(scores)
        r = rng.random() * total
        acc = 0.0
        for p, s in zip(population, scores):
            acc += s
            if acc >= r:
                return p
        return population[-1]

    if style == "novelty":
        # prefer candidates far from population centroid
        dim = len(population[0].weights)
        centroid = [
            sum(p.weights[i] for p in population) / len(population) for i in range(dim)
        ]

        def novelty(p: Program) -> float:
            return math.sqrt(sum((p.weights[i] - centroid[i]) ** 2 for i in range(dim)))

        weights = [novelty(p) + 1e-6 for p in population]
        total = sum(weights)
        r = rng.random() * total
        acc = 0.0
        for p, w in zip(population, weights):
            acc += w
            if acc >= r:
                return p
        return population[-1]

    if style == "ucb_parent":
        pulls = parent_pulls if parent_pulls is not None else {}
        total = sum(pulls.get(p.version, 0) for p in population) + 1
        best = population[0]
        best_score = float("-inf")
        for p in population:
            n = pulls.get(p.version, 0)
            fit = score_fn(p)
            if n <= 0:
                score = fit + 10.0  # force try unseen parents
            else:
                score = fit + math.sqrt(2.0 * math.log(total) / n)
            score += rng.random() * 1e-9
            if score > best_score:
                best_score = score
                best = p
        return best

    raise ValueError(f"unknown select_style {style}")
