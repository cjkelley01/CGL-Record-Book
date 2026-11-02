"""Read-only audit of ESPN historical weekly roster projections and actuals."""
import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path

from scripts.discover_espn_history import build_session, endpoint

def get_stat(player, week, source):
    matches = [s for s in player.get("stats", []) if isinstance(s, dict)
               and s.get("statSourceId") == source
               and s.get("scoringPeriodId") == week
               and s.get("statSplitTypeId") == 1
               and isinstance(s.get("appliedTotal"), (int, float))
               and not isinstance(s.get("appliedTotal"), bool)]
    return (matches[0]["appliedTotal"], len(matches)) if len(matches) == 1 else (None, len(matches))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", default="2024:6,2025:6,2026:6")
    parser.add_argument("--league-id", type=int, default=1877457250)
    parser.add_argument("--output", default="historical-projection-audit")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    session = build_session()
    rows, reports = [], []
    for item in args.weeks.split(","):
        season, week = map(int, item.strip().split(":"))
        report = {"season": season, "week": week}
        try:
            response = session.get(endpoint(args.league_id, season),
                                   params={"view": "mRoster", "scoringPeriodId": week},
                                   timeout=60)
            report["http_status"] = response.status_code
            response.raise_for_status()
            payload = response.json()
            teams = payload.get("teams", [])
            report["teams"] = len(teams)
            report["expected_teams"] = 14 if season >= 2026 else 12
            report["team_count_matches"] = len(teams) == report["expected_teams"]
            counter = Counter()
            for team in teams:
                entries = (team.get("roster") or {}).get("entries") or []
                counter["roster_entries"] += len(entries)
                for entry in entries:
                    player = ((entry.get("playerPoolEntry") or {}).get("player") or {})
                    projected, nproj = get_stat(player, week, 1)
                    actual, nactual = get_stat(player, week, 0)
                    if projected is not None:
                        counter["with_projection"] += 1
                    if actual is not None:
                        counter["with_actual"] += 1
                    if projected is not None and actual is not None:
                        counter["paired"] += 1
                    if nproj > 1: counter["duplicate_projection_records"] += 1
                    if nactual > 1: counter["duplicate_actual_records"] += 1
                    rows.append({
                        "season": season, "week": week, "team_id": team.get("id"),
                        "player_id": player.get("id", entry.get("playerId")),
                        "player_name": player.get("fullName"),
                        "position_id": player.get("defaultPositionId"),
                        "lineup_slot_id": entry.get("lineupSlotId"),
                        "projected": projected, "actual": actual,
                        "projection_records": nproj, "actual_records": nactual
                    })
            report.update(counter)
            report["status"] = "ok"
            print(json.dumps(report, sort_keys=True), flush=True)
        except Exception as exc:
            report["status"] = "error"
            report["error"] = f"{type(exc).__name__}: {str(exc)[:250]}"
            print(json.dumps(report, sort_keys=True), flush=True)
        reports.append(report)
    (output / "coverage.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    if rows:
        with (output / "player_weeks.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    # No raw ESPN payloads or credentials are included in the artifact.
    if not any(r.get("status") == "ok" for r in reports):
        raise SystemExit("All historical requests failed; inspect coverage.json.")
    if not any(r.get("paired", 0) for r in reports):
        raise SystemExit("No paired historical projected/actual points; inspect coverage.json.")

if __name__ == "__main__":
    main()
