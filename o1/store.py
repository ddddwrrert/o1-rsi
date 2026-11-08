from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .types import to_jsonable


class O1Store:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "islands").mkdir(exist_ok=True)
        (self.root / "policies").mkdir(exist_ok=True)
        self.events = self.root / "events.jsonl"
        if not self.events.exists():
            self.events.write_text("", encoding="utf-8")

    def _write_json(self, path: Path, obj: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(to_jsonable(obj), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def log(self, event: dict[str, Any]) -> None:
        with self.events.open("a", encoding="utf-8") as f:
            f.write(json.dumps(to_jsonable(event), ensure_ascii=False) + "\n")

    def save_tip(self, tip: Any, meta: dict[str, Any] | None = None) -> None:
        payload = {"tip": tip, **(meta or {})}
        self._write_json(self.root / "tip.json", payload)

    def save_island(self, island_id: str, payload: dict[str, Any]) -> None:
        self._write_json(self.root / "islands" / f"{island_id}.json", payload)

    def save_policy(self, version: str, payload: dict[str, Any]) -> None:
        safe = version.replace("/", "_")
        self._write_json(self.root / "policies" / f"{safe}.json", payload)

    def save_budget(self, snap: dict[str, Any]) -> None:
        self._write_json(self.root / "budget.json", snap)

    def save_report(self, report: dict[str, Any]) -> None:
        self._write_json(self.root / "report.json", report)
