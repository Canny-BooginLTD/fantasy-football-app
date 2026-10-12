"""Master orchestration layer for full-season ESPN imports and downstream exports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from watson.history_store import HistoricalDataStore
from watson.ingest import ingest_espn_history


@dataclass
class MasterProject:
    """Coordinates bulk ESPN ingestion and normalized exports for downstream apps."""

    league_id: str
    storage_path: Optional[str] = None

    def import_all_seasons(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        if start_year is not None and end_year is not None:
            for year in range(start_year, end_year + 1):
                snapshots.extend(
                    ingest_espn_history(self.league_id, year=year, storage_path=self.storage_path)
                )
            return snapshots

        snapshots.extend(ingest_espn_history(self.league_id, year=None, storage_path=self.storage_path))
        return snapshots

    def export_snapshot_bundle(self, output_path: str) -> str:
        store = HistoricalDataStore(storage_path=self.storage_path)
        payload = {
            "league_id": self.league_id,
            "snapshots": store.load_all(),
        }
        Path(output_path).write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
        return output_path

