from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ARM_IDS = (
    "repair",
    "neighborhood",
    "skeleton",
    "restart",
    "speed",
    "depth",
    "crossover",
)


@dataclass(frozen=True)
class Program:
    """Candidate solution: fixed-dim weight vector."""

    weights: tuple[float, ...]
    version: str
    parent_version: str | None = None
    island_id: str | None = None
    arm_id: str | None = None

    def as_list(self) -> list[float]:
        return list(self.weights)


@dataclass(frozen=True)
class IslandPolicy:
    """
    L1 citizen (light strategy individual): per-island search constitution.
    Changing this is a rare 'posting' event; daily work only updates arm stats.
    """

    island_id: str
    arm_menu: tuple[str, ...]
    select_style: str  # "fitness" | "novelty" | "ucb_parent"
    survive_k: int
    behavior_tag: str
    version: str
    parent_version: str | None = None
    status: str = "active"  # active | temp | retired

    def __post_init__(self) -> None:
        if not self.arm_menu:
            raise ValueError("arm_menu must be non-empty")
        bad = [a for a in self.arm_menu if a not in ARM_IDS]
        if bad:
            raise ValueError(f"unknown arms: {bad}")
        if self.select_style not in {"fitness", "novelty", "ucb_parent"}:
            raise ValueError(f"bad select_style: {self.select_style}")


@dataclass
class ArmStat:
    """L2 citizen stats, keyed per island (do not pool globally)."""

    arm_id: str
    pulls: int = 0
    total_reward: float = 0.0
    total_cost: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.pulls <= 0:
            return 0.0
        return self.total_reward / self.pulls

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "pulls": self.pulls,
            "total_reward": self.total_reward,
            "total_cost": self.total_cost,
            "mean_reward": self.mean_reward,
        }


@dataclass
class IslandState:
    island_id: str
    policy: IslandPolicy
    population: list[Program] = field(default_factory=list)
    arm_stats: dict[str, ArmStat] = field(default_factory=dict)
    stall_steps: int = 0
    best_fitness: float = float("-inf")
    generations: int = 0

    def ensure_arm_stats(self) -> None:
        for arm in self.policy.arm_menu:
            if arm not in self.arm_stats:
                self.arm_stats[arm] = ArmStat(arm_id=arm)
        # drop stats for arms no longer on the menu (keep history elsewhere if needed)
        self.arm_stats = {k: v for k, v in self.arm_stats.items() if k in self.policy.arm_menu}


@dataclass
class Split:
    public: tuple[str, ...]
    gate: tuple[str, ...]
    sealed: tuple[str, ...]


def to_jsonable(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
