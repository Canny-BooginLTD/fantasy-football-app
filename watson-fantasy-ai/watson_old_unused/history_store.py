"""Local storage for historical league snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tinydb import TinyDB
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without TinyDB installed
    TinyDB = None


class HistoricalDataStore:
    """Persist and load ESPN-derived historical snapshots locally."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or Path.home() / ".watson" / "historical_data.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.use_tinydb = TinyDB is not None
        self.db = None
        self.table = None

        if self.use_tinydb and self._looks_like_tinydb_file():
            self.db = TinyDB(self.storage_path)
            self.table = self.db.table("snapshots")
        elif self.use_tinydb and self._looks_like_legacy_json():
            legacy_snapshots = self._load_json_legacy()
            self.db = TinyDB(self.storage_path)
            self.table = self.db.table("snapshots")
            if legacy_snapshots:
                self.table.insert_multiple(legacy_snapshots)
        elif self.use_tinydb:
            self.db = TinyDB(self.storage_path)
            self.table = self.db.table("snapshots")

    def save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        if self.table is not None:
            self.table.insert(snapshot)
            return
        self._save_json([snapshot], append=True)

    def save_snapshots(self, snapshots: List[Dict[str, Any]]) -> None:
        if self.table is not None:
            self.table.insert_multiple(snapshots)
            return
        self._save_json(snapshots, append=True)

    def load_all(self) -> List[Dict[str, Any]]:
        if self.table is not None:
            return self.table.all()
        return self._load_json_legacy()

    def latest(self) -> Dict[str, Any]:
        snapshots = self.load_all()
        return snapshots[-1] if snapshots else {}

    def get_by_season(self, season: int) -> List[Dict[str, Any]]:
        snapshots = self.load_all()
        return [snapshot for snapshot in snapshots if snapshot.get("season") == season]

    def _looks_like_tinydb_file(self) -> bool:
        try:
            raw = self.storage_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return False
        return raw.startswith("{")

    def _looks_like_legacy_json(self) -> bool:
        try:
            raw = self.storage_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return False
        return raw.startswith("[")

    def _load_json_legacy(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            raw = self.storage_path.read_text(encoding="utf-8").strip()
            if not raw or raw.startswith("{"):
                return []
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def _save_json(self, snapshots: List[Dict[str, Any]], append: bool) -> None:
        payload = self._load_json_legacy() if append else []
        payload.extend(snapshots)
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
