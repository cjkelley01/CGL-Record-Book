"""Validate current-week waiver estimates and 84 future team-week lineups."""
import argparse
import json
from pathlib import Path
from scripts.analytics.espn_projections import (
    extract_weekly_means, roster_entries, starter_slots, waiver_replacements,
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-week", type=int, default=9)
    parser.add_argument("--end-week", type=int, default=14)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()
    root = args.data_root / "raw" / str(args.season)
    snapshot = json.loads((root / "current_week_free_agents.json").read_text(encoding="utf-8"))
    settings = json.loads((root / "league" / "mSettings.json").read_text(encoding="utf-8"))
    slots = starter_slots(settings)
    team_ids = set()
    rostered = set()
    for week in range(args.start_week, args.end_week + 1):
        payload = json.loads((root / "weeks" / f"{week:02d}" / "mRoster.json").read_text(encoding="utf-8"))
        for tid, entries in roster_entries(payload).items():
            team_ids.add(tid)
            for entry in entries:
                pid = (entry.get("playerPoolEntry") or {}).get("player", {}).get("id") or entry.get("playerId")
                if pid is not None:
                    rostered.add(int(pid))
    replacements = waiver_replacements(snapshot["players"], snapshot["projection_week"],
                                        rostered, slots)
    by_slot = {p["eligible_slots"][0]: round(p["projection"], 2) for p in replacements}
    print("Waiver source week:", snapshot["projection_week"])
    print("Top-three means by ESPN slot:", json.dumps(by_slot, sort_keys=True))
    result = extract_weekly_means(args.data_root, args.season,
                                  range(args.start_week, args.end_week + 1),
                                  sorted(team_ids))
    for row in result["coverage"]:
        print(f"Week {row['week']}: {row.get('teams_with_valid_lineups', 0)}/{row.get('teams_expected', len(team_ids))} valid; "
              f"modeled teams={row.get('teams_using_waiver_replacements', 0)}; "
              f"status={row['status']}")
        for failure in row.get("teams_without_valid_lineups", []):
            print(f"  Team {failure['team_id']}: {failure['reason']}")
    print("FORECAST READY:", result["ready"])

if __name__ == "__main__":
    main()
