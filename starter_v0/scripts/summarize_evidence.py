"""Build CSV evidence from saved, real eval runs. Does not call any provider."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FIELDS = ["version", "author", "changed_artifact", "artifact_version", "prompt_hash", "tools_hash",
                  "reason", "hypothesis", "metric_before", "metric_after", "run_file"]


def export_evidence(root: Path = ROOT) -> tuple[int, int]:
    plan_path = root / "artifacts" / "versions" / "plan.json"
    plans = {item["version"]: item for item in json.loads(plan_path.read_text(encoding="utf-8"))["versions"]} if plan_path.exists() else {}
    rows, cases = [], []
    previous: dict[tuple[str, str, str], dict] = {}
    for path in sorted((root / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        summary = run["summary"]
        version = run["version"]
        plan = plans.get(version, {})
        key = (run["provider"], run.get("model") or "", run["suite"])
        complete = summary["provider_error_cases"] == 0
        reason = plan.get("reason", "Original baseline")
        if not complete:
            reason += f" [INCOMPLETE: {summary['provider_error_cases']} provider errors; not a full baseline/comparison]"
        rows.append({"version": version, "author": "team", "changed_artifact": "baseline" if version == "v0" else "system_prompt.md;tools.yaml",
                     "artifact_version": run["artifact_version"], "prompt_hash": run["prompt_hash"], "tools_hash": run["tools_hash"],
                     "reason": f"{reason}; provider={run['provider']}; model={run.get('model')}; suite={run['suite']}",
                     "hypothesis": plan.get("hypothesis", "Measure the starter before optimization."),
                     "metric_before": json.dumps(previous[key], sort_keys=True) if key in previous else "",
                     "metric_after": json.dumps(summary, sort_keys=True), "run_file": path.relative_to(root).as_posix()})
        if complete:
            previous[key] = summary
        for case in run["results"]:
            result = case["result"]
            cases.append({"run_file": path.relative_to(root).as_posix(), "version": version, "suite": run["suite"],
                          "case_id": case["id"], "multiturn": case.get("is_multiturn", False),
                          "passed": result["passed"], "failure_type": result.get("failure_type") or "",
                          "observed_mismatch": result.get("observed_mismatch") or "",
                          "actual_tool_calls": json.dumps(result.get("actual_tool_calls", []), ensure_ascii=False),
                          "failures": json.dumps(result.get("failures", []), ensure_ascii=False)})
    (root / "analysis").mkdir(exist_ok=True)
    with (root / "artifacts" / "version_log.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=VERSION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with (root / "analysis" / "eval_cases.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["run_file", "version", "suite", "case_id", "multiturn", "passed",
                                                "failure_type", "observed_mismatch", "actual_tool_calls", "failures"])
        writer.writeheader()
        writer.writerows(cases)
    return len(rows), len(cases)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    runs, cases = export_evidence(args.root)
    print(f"Exported {runs} real runs, {cases} case results. Prepared versions without runs are omitted.")


if __name__ == "__main__":
    main()
