from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Budget:
    """
    Official eval tickets. meta=0: no separate account for inventing new providers.
    """

    total: int
    island_search: int = 0
    migrate: int = 0
    policy_trial: int = 0
    sealed: int = 0
    meta: int = 0

    caps: dict[str, float] = field(
        default_factory=lambda: {
            "island_search": 0.82,
            "migrate": 0.05,
            "policy_trial": 0.08,
            "sealed": 0.05,
            "meta": 0.0,
        }
    )

    def spent(self) -> int:
        return self.island_search + self.migrate + self.policy_trial + self.sealed + self.meta

    def remaining_total(self) -> int:
        return max(0, self.total - self.spent())

    def account_cap(self, account: str) -> int:
        return int(self.total * self.caps.get(account, 0.0))

    def remaining(self, account: str) -> int:
        used = getattr(self, account)
        return max(0, self.account_cap(account) - used)

    def can_afford(self, account: str, n: int = 1) -> bool:
        if account == "meta" and self.caps.get("meta", 0.0) <= 0:
            return False
        return self.remaining_total() >= n and self.remaining(account) >= n

    def charge(self, account: str, n: int = 1) -> None:
        if n <= 0:
            return
        if account == "meta" and self.caps.get("meta", 0.0) <= 0:
            raise RuntimeError("meta account is frozen at 0")
        if not self.can_afford(account, n):
            raise RuntimeError(f"cannot charge {n} to {account}")
        setattr(self, account, getattr(self, account) + n)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "spent": self.spent(),
            "remaining_total": self.remaining_total(),
            "accounts": {
                "island_search": self.island_search,
                "migrate": self.migrate,
                "policy_trial": self.policy_trial,
                "sealed": self.sealed,
                "meta": self.meta,
            },
            "caps": dict(self.caps),
        }
