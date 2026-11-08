from __future__ import annotations

from .types import IslandPolicy


def default_island_policies() -> list[IslandPolicy]:
    """Three deliberately non-identical menus (anti-monoculture)."""
    return [
        IslandPolicy(
            island_id="A_repair",
            arm_menu=("repair", "neighborhood", "speed"),
            select_style="fitness",
            survive_k=5,
            behavior_tag="repair",
            version="P-A0",
        ),
        IslandPolicy(
            island_id="B_struct",
            arm_menu=("skeleton", "depth", "restart"),
            select_style="novelty",
            survive_k=5,
            behavior_tag="structure",
            version="P-B0",
        ),
        IslandPolicy(
            island_id="C_mix",
            arm_menu=("repair", "neighborhood", "skeleton", "crossover", "depth"),
            select_style="ucb_parent",
            survive_k=5,
            behavior_tag="mixed",
            version="P-C0",
        ),
    ]


def backup_menus() -> dict[str, tuple[str, ...]]:
    """Alternate menus for stall-triggered policy trial."""
    return {
        "A_repair": ("repair", "depth", "crossover"),
        "B_struct": ("skeleton", "neighborhood", "speed", "restart"),
        "C_mix": ("restart", "speed", "repair", "neighborhood"),
    }
