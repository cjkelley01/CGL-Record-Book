"""Read-only, credential-safe historical ESPN data availability probe.

This measures what ESPN returns *today*, not what it showed at a past cutoff.
No retrieved player/roster payloads are persisted.
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.discover_espn_history import build_session, endpoint


def stat_summary(player, target):
    stats = player.get("stats") or []
    projections = [s for s in stats if isinstance(s, dict)
                   and s.get("statSourceId") == 1
                   and s.get("statSplitTypeId") == 1
                   and s.get("scoringPeriodId") == target
                   and isinstance(s.get("appliedTotal"), (int, float))
                   and not isinstance(s.get("appliedTotal"), bool)]
    return len(projections)


def summarize_roster(payload, target):
    teams = payload.get("teams") or []
    counts = Counter()
    roster_sets = {}
    for team in teams:
        entries = (team.get("roster") or {}).get("entries") or []
        ids = set()
        for entry in entries:
            player = ((entry.get("playerPoolEntry") or {}).get("player") or {})
            pid = player.get("id", entry.get("playerId"))
            if pid is not None:
                ids.add(int(pid))
            counts["roster_entries"] += 1
            n = stat_summary(player, target)
            counts["target_week_projection_present"] += int(n == 1)
            counts["target_week_projection_missing"] += int(n == 0)
            counts["target_week_projection_ambiguous"] += int(n > 1)
        roster_sets[int(team["id"])] = ids
    return {"team_count": len(teams), **dict(counts)}, roster_sets


def audit(session, league_id, season, cutoff, target):
    """Compare historical roster queries; never equate retrospective data with archived snapshots."""
    result = {"season": season, "cutoff_week": cutoff, "target_week": target,
              "source": "live ESPN API queried at audit execution",
              "point_in_time_projection_verified": False,
              "point_in_time_roster_verified": False}
    rosters = {}
    for label, week in (("cutoff", cutoff), ("target", target)):
        try:
            response = session.get(endpoint(league_id, season),
                                   params={"view": "mRoster", "scoringPeriodId": week},
                                   timeout=60)
            result[label + "_http_status"] = response.status_code
            response.raise_for_status()
            summary, roster_sets = summarize_roster(response.json(), target)
            result[label + "_coverage"] = summary
            rosters[label] = roster_sets
        except Exception as exc:
            result[label + "_error"] = type(exc).__name__ + ": " + str(exc)[:180]
    if len(rosters) == 2:
        common = set(rosters["cutoff"]) & set(rosters["target"])
        result["common_teams"] = len(common)
        result["teams_with_roster_difference"] = sum(
            rosters["cutoff"][tid] != rosters["target"][tid] for tid in common)
        result["roster_comparison_note"] = (
            "Different roster responses indicate week-dependent API state, "
            "NOT proof of historically archived cutoff-day ownership.")
    result["interpretation"] = (
        "Retrospectively returned projections cannot be treated as forecasts "
        "available at the historical cutoff without a dated pregame snapshot.")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", default="2024:7:10,2024:10:13,2025:7:10,2025:10:13",
                        help="Comma-separated season:cutoff_week:target_week")
    parser.add_argument("--league-id", type=int, default=1877457250)
    parser.add_argument("--output", default="historical-availability-audit")
    args = parser.parse_args()
    session = build_session()
    rows = []
    for item in args.pairs.split(","):
        season, cutoff, target = (int(x) for x in item.strip().split(":"))
        if cutoff >= target:
            parser.error("Each target week must be later than its cutoff")
        row = audit(session, args.league_id, season, cutoff, target)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "status": "data_observed" if any("cutoff_coverage" in r for r in rows)
              else "no_successful_queries",
              "findings": rows,
              "limitations": [
                  "This is a retrospective API availability audit, not a point-in-time backtest.",
                  "No API response timestamp establishes when a projection was originally published.",
                  "Weekly roster differences do not prove a roster snapshot was available at the earlier cutoff.",
                  "No credentials or raw ESPN player payloads are included in the report.",
                  "Historical future-week projections remain unverified without timestamped captures."
              ]}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] == "no_successful_queries":
        raise SystemExit("No successful historical ESPN queries; inspect report artifact.")


if __name__ == "__main__":
    main()
