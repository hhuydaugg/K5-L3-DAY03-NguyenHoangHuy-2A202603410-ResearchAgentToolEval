"""Prepared artifacts must never become fabricated evaluation evidence."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_evidence import export_evidence


def test_only_saved_runs_enter_version_log_and_partial_metrics_are_flagged(tmp_path):
    artifacts = tmp_path / "artifacts"
    (artifacts / "versions").mkdir(parents=True)
    (artifacts / "versions" / "plan.json").write_text(json.dumps({"versions": [
        {"version": "v1", "reason": "prepared", "hypothesis": "not yet measured"},
    ]}), encoding="utf-8")
    runs = tmp_path / "runs"
    runs.mkdir()
    payload = {"version": "v0", "provider": "fake", "model": "test-only", "suite": "base",
               "artifact_version": "v0+test", "prompt_hash": "test-prompt", "tools_hash": "test-tools",
               "summary": {"provider_error_cases": 1, "measured_cases": 1, "case_accuracy": 1.0}, "results": []}
    (runs / "01.json").write_text(json.dumps(payload), encoding="utf-8")
    payload["version"] = "v1"
    payload["summary"] = {"provider_error_cases": 0, "measured_cases": 2, "case_accuracy": 0.5}
    (runs / "02.json").write_text(json.dumps(payload), encoding="utf-8")
    assert export_evidence(tmp_path) == (2, 0)
    with (artifacts / "version_log.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert [row["version"] for row in rows] == ["v0", "v1"]
    assert "INCOMPLETE" in rows[0]["reason"]
    # A partial run is not silently used as a complete before/after baseline.
    assert rows[1]["metric_before"] == ""
    (runs / "02.json").unlink()
    export_evidence(tmp_path)
    with (artifacts / "version_log.csv").open(encoding="utf-8", newline="") as file:
        assert [row["version"] for row in csv.DictReader(file)] == ["v0"]
