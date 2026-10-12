"""Stable export contract for downstream fantasy-football apps."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class ExportBundle:
    """Normalized data bundle suitable for external consumers."""

    league_id: str
    snapshots: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

