"""Inspect ESPN future-week roster projection coverage without publishing private rosters.

Use locally downloaded data/raw/2026/weeks/{week}/mRoster.json and mBoxscore.json.
No ESPN credentials or raw payloads are included in the report.
"""
import argparse
import json
from pathlib import Path


def inspect_week(root, week):
    report = {"week": week, "files": {}, "projection_records": 0,
              "projected_player_ids": 0, "slot_ids": [], "stat_sources": []}
    player_ids, slots, sources = set(), set(), set()
    for view in ("mRoster", "mBoxscore"):
        path = root / "raw" / "2026" / "weeks" / f"{week:02d}" / f"{view}.json"
        if not path.exists():
            report["files"][view] = "missing"
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        report["files"][view] = "available"
        def visit(node, player_id=None):
            if isinstance(node, dict):
                pid = node.get("id", player_id)
                if "lineupSlotId" in node:
                    slots.add(str(node["lineupSlotId"]))
                if isinstance(node.get("stats"), list):
                    for stat in node["stats"]:
                        if not isinstance(stat, dict):
                            continue
                        if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == week and isinstance(stat.get("appliedTotal"), (int, float)):
                            report["projection_records"] += 1
                            if pid is not None:
                                player_ids.add(str(pid))
                            sources.add(str(stat.get("statSourceId")))
                for value in node.values():
                    visit(value, pid)
            elif isinstance(node, list):
                for value in node:
                    visit(value, player_id)
        visit(payload)
    report["projected_player_ids"] = len(player_ids)
    report["slot_ids"] = sorted(slots)
    report["stat_sources"] = sorted(sources)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--start-week", type=int, default=9)
    parser.add_argument("--end-week", type=int, default=18)
    parser.add_argument("--output", type=Path, default=Path("data/reports/forecast_projection_coverage.json"))
    args = parser.parse_args()
    report = {"season": 2026, "weeks": [inspect_week(args.data_root, week)
              for week in range(args.start_week, args.end_week + 1)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not any(row["projection_records"] for row in report["weeks"]):
        print("No future-week player projections found. Roster-aware simulation must remain disabled until verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
