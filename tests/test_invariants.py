from __future__ import annotations

from o1.budget import Budget
from o1.policies import default_island_policies
from o1.types import ARM_IDS


def test_meta_frozen():
    b = Budget(total=100)
    assert b.can_afford("meta", 1) is False
    try:
        b.charge("meta", 1)
        raised = False
    except RuntimeError:
        raised = True
    assert raised


def test_default_menus_disjointish():
    pols = default_island_policies()
    assert len(pols) == 3
    menus = [set(p.arm_menu) for p in pols]
    # not all identical
    assert not (menus[0] == menus[1] == menus[2])
    for p in pols:
        assert set(p.arm_menu) <= set(ARM_IDS)
