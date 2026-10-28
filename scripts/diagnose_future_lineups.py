"""Report legal starting-lineup coverage from locally saved ESPN future rosters.

Does not create synthetic replacement scores or change forecast outputs.
"""
import argparse
import json
from pathlib import Path

from scripts.analytics.espn_projections import (
    normalized_players, roster_entries, starter_slots,
)
from scripts.analytics.optimal_lineup import optimize_lineup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-week", type=int, default=9)
    parser.add_argument("--end-week", type=int, default=14)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()

    root = args.data_root / "raw" / str(args.season)
    settings = json.loads((root / "league" / "mSettings.json").read_text(encoding="utf-8"))
    schedule = json.loads((root / "nfl_schedule.json").read_text(encoding="utf-8"))
    slots = starter_slots(settings)
    total_valid = total_checked = 0
    for week in range(args.start_week, args.end_week + 1):
        playing = set(map(int, schedule.get(str(week), [])))
        if not 26 <= len(playing) <= 32:
            print(f"Week {week}: missing verified NFL schedule")
            continue
        path = root / "weeks" / f"{week:02d}" / "mRoster.json"
        if not path.exists():
            print(f"Week {week}: missing mRoster.json")
            continue
        rosters = roster_entries(json.loads(path.read_text(encoding="utf-8")))
        failures = []
        valid = 0
        for team_id, entries in sorted(rosters.items()):
            total_checked += 1
            players = normalized_players(entries, week, skip_missing=True, playing_teams=playing)
            try:
                optimize_lineup(players, slots)
                valid += 1
                total_valid += 1
            except ValueError as exc:
                failures.append(f"{team_id} ({str(exc)[:65]})")
        print(f"Week {week}: {valid}/{len(rosters)} legal lineups"
              + (f"; need replacements: {', '.join(failures)}" if failures else ""))
    print(f"TOTAL: {total_valid}/{total_checked} legal team-weeks")


if __name__ == "__main__":
    main()
