#!/usr/bin/env python3
"""Refresh the active ESPN season and rebuild the CGL record book."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--league-id", type=int, default=1877457250)
    parser.add_argument("--end-week", type=int, default=18)
    return parser.parse_args()


def run(command: list[str], label: str, cwd: Path) -> None:
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run(command, check=False, cwd=cwd)
    if result.returncode:
        raise SystemExit(f"\nUpdate stopped: {label.lower()} failed.")


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent

    run([
        sys.executable, str(root / "scripts" / "discover_espn_history.py"),
        "--league-id", str(args.league_id),
        "--seasons", str(args.season),
        "--end-week", str(args.end_week),
    ], f"Downloading {args.season} ESPN data", root)

    report_path = root / "data" / "reports" / "espn_history_discovery.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    failures = [row for row in report["results"] if not row["ok"]]
    if failures:
        print(f"\nUpdate stopped: {len(failures)} ESPN requests failed.")
        for row in failures[:10]:
            print(f"- {row['season']} {row['scope']} {row['view']}: {row['error']}")
        if len(failures) > 10:
            print(f"- ...and {len(failures) - 10} more. See {report_path}.")
        return 1

    run([sys.executable, str(root / "scripts" / "build_core_history.py")], "Rebuilding records and leaderboards", root)

    history_path = root / "app" / "data" / "core_history.json"
    history = json.loads(history_path.read_text(encoding="utf-8"))
    season = next((row for row in history["seasons"] if row["season"] == args.season), None)
    if season is None:
        raise SystemExit(f"Update stopped: {args.season} is missing from the rebuilt history.")

    status = "complete" if season["is_complete"] else "in progress"
    print("\n=== Update complete ===")
    print(f"{args.season} is {status}; official results are current through Week {season['through_week']}.")
    print("The website data is ready. Run: corepack pnpm dev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
