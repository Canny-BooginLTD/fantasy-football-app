"""Tests for the master project orchestration layer."""

from watson.export_contract import ExportBundle
from watson.master_project import MasterProject


def test_export_bundle_to_dict():
    bundle = ExportBundle(league_id="123", snapshots=[{"season": 2025}])
    data = bundle.to_dict()
    assert data["league_id"] == "123"
    assert data["snapshots"][0]["season"] == 2025


def test_master_project_export_snapshot_bundle(tmp_path):
    master = MasterProject(league_id="123", storage_path=str(tmp_path / "history.json"))
    master.export_snapshot_bundle(str(tmp_path / "bundle.json"))
    assert (tmp_path / "bundle.json").exists()

