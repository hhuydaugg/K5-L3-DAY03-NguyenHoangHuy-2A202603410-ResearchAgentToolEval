"""Check submission evidence offline; do not call providers or rewrite raw logs."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import TOOL_FUNCTIONS, load_tool_declarations


def main() -> None:
    checks = []

    def check(name, ok, detail):
        checks.append({"name": name, "passed": bool(ok), "detail": detail})

    declarations = load_tool_declarations(ROOT / "artifacts/tools.yaml")
    check("at_least_five_tools", len(declarations) >= 5, len(declarations))
    names = {tool["name"] for tool in declarations}
    check("registry_and_tool_docs", all(name in TOOL_FUNCTIONS and
          (ROOT / "tools" / name / "TOOL.md").is_file() for name in names), sorted(names))
    group = json.loads((ROOT / "data/eval_group.json").read_text())["cases"]
    multi = sum(bool(case.get("turns")) for case in group)
    check("group_five_single_five_multi", len(group) >= 10 and multi >= 5 and len(group)-multi >= 5,
          {"single": len(group)-multi, "multi": multi})
    check("new_tool_eval_case", any(call["name"] == "deduplicate_sources" for case in group
          for call in case.get("expect", {}).get("tool_calls", [])), "deduplicate_sources")
    rows = list(csv.DictReader((ROOT / "artifacts/version_log.csv").open(encoding="utf-8")))
    check("version_history", {"v0", "v1", "v2", "v3"} <= {row["version"] for row in rows}, len(rows))
    missing = [row["run_file"] for row in rows if row["run_file"] and not (ROOT / row["run_file"]).is_file()]
    check("version_log_paths_exist", not missing, missing)
    validation = json.loads((ROOT / "analysis/current_validation.json").read_text())
    hashes = {key: hashlib.sha256((ROOT / "artifacts" / filename).read_bytes()).hexdigest()
              for key, filename in [("prompt_hash", "system_prompt.md"), ("tools_hash", "tools.yaml")]}
    for suite in ["base", "group", "robustness", "stability", "author_stability"]:
        path = ROOT / validation[suite]
        data = json.loads(path.read_text())
        check(f"{suite}_evidence_matches_current", all(data.get(key) == value for key, value in hashes.items()),
              {"path": validation[suite], "summary": data["summary"]})
    live = json.loads((ROOT / validation["live_transcript"]).read_text())
    check("live_evidence_matches_current", all(live.get(key) == value for key, value in hashes.items()),
          {"path": validation["live_transcript"], "turns": len(live.get("turns", []))})
    for filename in ["system_prompt.md", "tools.yaml"]:
        check(f"snapshot_{filename}", (ROOT / "artifacts" / filename).read_bytes() ==
              (ROOT / "artifacts/current" / filename).read_bytes(), filename)
    result = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "checks": checks, "automated_checks_passed": all(c["passed"] for c in checks),
              "manual_remaining": ["Public UI URL on a second device/network",
                                   "Active policy/paper_text/timeframe descriptions need completion; HTTP 402 blocked fresh evaluation",
                                   "Verify one-change-per-version requirement against inherited group v1; do not rewrite history",
                                   "Actual demo and historical 16:30 deadline cannot be certified offline"],
              "limitations": "Hash/path checks do not certify source accuracy, delivery success or rubric acceptance."}
    output = ROOT / "analysis/submission_audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{sum(c['passed'] for c in checks)}/{len(checks)} offline submission checks passed. {output}")
    for item in checks:
        if not item["passed"]:
            print(f"FAIL: {item['name']}")
    raise SystemExit(0 if result["automated_checks_passed"] else 1)


if __name__ == "__main__":
    main()
