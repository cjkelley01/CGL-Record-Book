"""Audit whether every CGL team has a legal ESPN-projected lineup each future week.

Only aggregate counts and error categories are published; no roster contents.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.analytics.espn_projections import normalized_players, roster_entries, starter_slots
from scripts.analytics.optimal_lineup import optimize_lineup


def audit(data_root, season, weeks):
    root = Path(data_root) / "raw" / str(season)
    settings = json.loads((root / "league" / "mSettings.json").read_text())
    slots = starter_slots(settings)
    teams = json.loads((root / "league" / "mTeam.json").read_text())
    team_ids = {int(t["id"]) for t in teams["teams"]}
    if not team_ids:
        raise ValueError("No league teams found")
    results = []
    for week in weeks:
        path = root / "weeks" / f"{week:02d}" / "mRoster.json"
        if not path.exists():
            results.append({"week": week, "expected_teams": len(team_ids),
                            "valid_lineups": 0, "errors": {"missing_week_file": len(team_ids)}})
            continue
        rosters = roster_entries(json.loads(path.read_text()))
        errors = Counter()
        valid = 0
        for tid in sorted(team_ids):
            entries = rosters.get(tid)
            if not entries:
                errors["missing_team_roster"] += 1
                continue
            try:
                optimize_lineup(normalized_players(entries, week), slots)
                valid += 1
            except (ValueError, TypeError, KeyError) as exc:
                msg = str(exc)
                if "weekly ESPN projection" in msg:
                    errors["missing_or_ambiguous_player_projection"] += 1
                elif "No legal lineup" in msg or "Insufficient available" in msg:
                    errors["incomplete_eligible_lineup"] += 1
                else:
                    errors["other_lineup_validation_error"] += 1
        results.append({"week": week, "expected_teams": len(team_ids),
                        "valid_lineups": valid, "errors": dict(sorted(errors.items()))})
    return {"season": season, "starting_slots": sorted(slots),
            "weeks": results,
            "ready": all(x["valid_lineups"] == len(team_ids) for x in results)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-week", type=int, default=9)
    parser.add_argument("--end-week", type=int, default=18)
    parser.add_argument("--output", type=Path, default=Path("data/reports/lineup_projection_readiness.json"))
    args = parser.parse_args()
    report = audit(args.data_root, args.season, range(args.start_week, args.end_week + 1))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0  # Incomplete projections are a finding, not a refresh failure.


if __name__ == "__main__":
    raise SystemExit(main())
