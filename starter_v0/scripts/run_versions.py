"""Run saved version snapshots sequentially and refresh the evidence CSVs."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from summarize_evidence import export_evidence

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["gemini", "openrouter", "openai", "anthropic", "ollama"], default="gemini")
    parser.add_argument("--model")
    parser.add_argument("--versions", nargs="+", choices=["v0", "v1", "v2", "v3"], default=["v1", "v2", "v3"])
    parser.add_argument("--include-group", action="store_true", help="Run group suite with the last selected snapshot.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without calling APIs or changing run evidence.")
    args = parser.parse_args()
    tasks = [(version, "base") for version in args.versions]
    if args.include_group:
        if args.versions[-1] == "v0":
            parser.error("The group suite uses deduplicate, which is not in the original v0 tool snapshot.")
        tasks.append((args.versions[-1], "group"))
    for version, suite in tasks:
        snapshot = ROOT / "artifacts" / "versions" / version
        for name in ("system_prompt.md", "tools.yaml"):
            if not (snapshot / name).exists():
                parser.error(f"Missing snapshot file: {snapshot / name}")
        command = [sys.executable, str(ROOT / "run_eval.py"), "--provider", args.provider,
                   "--version", version, "--suite", suite, "--eval-cases", str(ROOT / "data" / f"eval_{suite}.json"),
                   "--system-prompt", str(snapshot / "system_prompt.md"), "--tools", str(snapshot / "tools.yaml")]
        if args.model:
            command.extend(["--model", args.model])
        print(subprocess.list2cmdline(command) if sys.platform == "win32" else shlex.join(command), flush=True)
        if args.dry_run:
            continue
        before = set((ROOT / "runs").glob("*.json"))
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
        new_runs = set((ROOT / "runs").glob("*.json")) - before
        export_evidence(ROOT)
        if len(new_runs) != 1:
            raise SystemExit("Could not identify exactly one new run. Check runs/ before continuing.")
        run = json.loads(next(iter(new_runs)).read_text(encoding="utf-8"))
        if run["summary"]["provider_error_cases"]:
            raise SystemExit("Stopped: provider errors remain. Evidence was saved; resolve quota/connectivity before the next version.")


if __name__ == "__main__":
    main()
