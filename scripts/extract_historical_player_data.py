"""Read-only historical player-week extraction and field availability audit."""
import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import requests
from scripts.discover_espn_history import build_session, endpoint

def points(player, week, source):
    matches = [s for s in player.get("stats", []) if isinstance(s, dict)
               and s.get("statSourceId") == source
               and s.get("statSplitTypeId") == 1
               and s.get("scoringPeriodId") == week
               and isinstance(s.get("appliedTotal"), (int, float))
               and not isinstance(s.get("appliedTotal"), bool)]
    return (matches[0]["appliedTotal"] if len(matches) == 1 else None, len(matches))

def get_week(session, league, season, week):
    last_error = None
    for attempt in range(3):
        try:
            r = session.get(endpoint(league, season),
                            params={"view": "mRoster", "scoringPeriodId": week},
                            timeout=60)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise last_error

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--league-id", type=int, default=1877457250)
    p.add_argument("--seasons", default="2024:18,2025:18,2026:8",
                   help="Comma-separated season:last-completed-week")
    p.add_argument("--output", default="historical-player-dataset")
    args = p.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    session = build_session()
    fields = ["season", "week", "team_id", "player_id", "player_name",
              "position_id", "pro_team_id", "lineup_slot_id", "eligible_slots",
              "injury_status", "projected", "actual", "projection_records",
              "actual_records", "has_projection", "has_actual"]
    rows, weeks, field_counts, stat_keys = [], [], Counter(), Counter()
    stat_source_counts = Counter()
    for spec in args.seasons.split(","):
        season, last_week = map(int, spec.strip().split(":"))
        for week in range(1, last_week + 1):
            report = {"season": season, "week": week}
            try:
                payload = get_week(session, args.league_id, season, week)
                teams = payload.get("teams", [])
                expected = 14 if season == 2026 else 12
                report["teams"] = len(teams)
                report["expected_teams"] = expected
                if len(teams) != expected:
                    raise ValueError(f"Expected {expected} teams, got {len(teams)}")
                counts = Counter()
                for team in teams:
                    entries = (team.get("roster") or {}).get("entries") or []
                    counts["roster_entries"] += len(entries)
                    for entry in entries:
                        player = ((entry.get("playerPoolEntry") or {}).get("player") or {})
                        proj, np = points(player, week, 1)
                        actual, na = points(player, week, 0)
                        counts["projected"] += proj is not None
                        counts["actual"] += actual is not None
                        counts["paired"] += proj is not None and actual is not None
                        counts["positive_projection_pairs"] += proj is not None and proj > 0 and actual is not None
                        counts["zero_projection_missing_actual"] += proj == 0 and actual is None
                        counts["missing_projection"] += proj is None
                        counts["missing_actual"] += actual is None
                        counts["duplicate_projection"] += np > 1
                        counts["duplicate_actual"] += na > 1
                        for key in player:
                            field_counts["player." + key] += 1
                        for key in entry:
                            field_counts["entry." + key] += 1
                        for s in player.get("stats", []):
                            if isinstance(s, dict):
                                for key in s: stat_keys[key] += 1
                                stat_source_counts[str((s.get("statSourceId"), s.get("statSplitTypeId")))] += 1
                        rows.append({
                            "season": season, "week": week, "team_id": team.get("id"),
                            "player_id": player.get("id", entry.get("playerId")),
                            "player_name": player.get("fullName"),
                            "position_id": player.get("defaultPositionId"),
                            "pro_team_id": player.get("proTeamId"),
                            "lineup_slot_id": entry.get("lineupSlotId"),
                            "eligible_slots": json.dumps(player.get("eligibleSlots")),
                            "injury_status": player.get("injuryStatus"),
                            "projected": proj, "actual": actual,
                            "projection_records": np, "actual_records": na,
                            "has_projection": proj is not None, "has_actual": actual is not None
                        })
                report.update(counts)
                report["status"] = "ok"
            except Exception as exc:
                report["status"] = "error"
                report["error"] = f"{type(exc).__name__}: {str(exc)[:220]}"
            weeks.append(report)
            print(json.dumps(report, sort_keys=True), flush=True)
            time.sleep(0.15)
    with (out / "player_weeks.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (out / "weekly_coverage.csv").open("w", newline="", encoding="utf-8") as f:
        columns = ["season", "week", "status", "teams", "expected_teams", "roster_entries",
                   "projected", "actual", "paired", "positive_projection_pairs",
                   "zero_projection_missing_actual", "missing_projection",
                   "missing_actual", "duplicate_projection", "duplicate_actual", "error"]
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(weeks)
    (out / "field_inventory.json").write_text(json.dumps({
        "player_field_occurrences": dict(field_counts.most_common()),
        "stat_field_occurrences": dict(stat_keys.most_common()),
        "stat_source_split_occurrences": dict(stat_source_counts.most_common()),
        "note": "Field presence only; not proof of historical point-in-time correctness."
    }, indent=2), encoding="utf-8")
    summary = {
        "requested_weeks": len(weeks),
        "successful_weeks": sum(w["status"] == "ok" for w in weeks),
        "failed_weeks": [w for w in weeks if w["status"] != "ok"],
        "total_player_weeks": len(rows),
        "unique_player_ids": len({(r["player_id"]) for r in rows}),
        "paired_player_weeks": sum(r["has_projection"] and r["has_actual"] for r in rows),
        "positive_projection_pairs": sum(r["has_projection"] and r["projected"] > 0 and r["has_actual"] for r in rows),
        "caveat": "Historical ESPN projections may be revised; no pregame snapshot provenance verified. Missing actual is not zero."
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("SUMMARY", json.dumps(summary), flush=True)
    if summary["failed_weeks"]:
        raise SystemExit("Some weeks failed. See weekly_coverage.csv; partial artifact preserved.")
    if not summary["paired_player_weeks"]:
        raise SystemExit("No paired observations found.")

if __name__ == "__main__":
    main()
