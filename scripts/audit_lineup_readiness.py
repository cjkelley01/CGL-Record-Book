"""Audit whether every CGL team has a legal ESPN-projected lineup each future week.

Only aggregate counts and error categories are published; no roster contents.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.analytics.espn_projections import extract_weekly_means, starter_slots
from scripts.analytics.optimal_lineup import optimize_lineup


def audit(data_root, season, weeks):
    """Use the same lineup and waiver checks as the published forecast."""
    weeks = list(weeks)
    root = Path(data_root) / "raw" / str(season)
    settings = json.loads((root / "league" / "mSettings.json").read_text())
    slots = starter_slots(settings)
    teams = json.loads((root / "league" / "mTeam.json").read_text())
    team_ids = sorted(int(t["id"]) for t in teams["teams"])
    if not team_ids:
        raise ValueError("No league teams found")
    result = extract_weekly_means(data_root, season, weeks, team_ids)
    rows = []
    for row in result["coverage"]:
        rows.append({"week": row["week"], "expected_teams": len(team_ids),
                     "valid_lineups": row.get("teams_with_valid_lineups", 0),
                     "waiver_pool_verified": row.get("waiver_pool_verified", False),
                     "teams_requiring_replacements": row.get("teams_requiring_replacements", []),
                     "teams_without_valid_lineups": row.get("teams_without_valid_lineups", []),
                     "status": row["status"]})
    return {"season": season, "starting_slots": sorted(slots),
            "weeks": rows, "ready": result["ready"]}


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
