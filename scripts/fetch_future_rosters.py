"""Refresh future-week ESPN mRoster projections for every fantasy team.

This is a read-only ESPN request. A week is written only after validating all
expected teams and reporting exact target-week stat coverage. Existing files
are preserved on incomplete responses.
"""
import argparse
import json
from pathlib import Path

from scripts.discover_espn_history import DEFAULT_LEAGUE_ID, build_session, endpoint


def weekly_projection(player, week):
    matches = [
        stat for stat in player.get("stats", [])
        if isinstance(stat, dict)
        and stat.get("statSourceId") == 1
        and stat.get("statSplitTypeId") == 1
        and stat.get("scoringPeriodId") == week
        and isinstance(stat.get("appliedTotal"), (int, float))
        and not isinstance(stat.get("appliedTotal"), bool)
    ]
    return len(matches) == 1


def fetch_week(session, league_id, season, week, output, expected_teams=14):
    response = session.get(
        endpoint(league_id, season),
        params={"view": "mRoster", "scoringPeriodId": week},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    teams = payload.get("teams") if isinstance(payload, dict) else None
    if not isinstance(teams, list) or len(teams) != expected_teams:
        raise ValueError(f"Expected {expected_teams} teams, got {len(teams) if isinstance(teams, list) else 'invalid response'}")
    ids = [team.get("id") for team in teams]
    if len(set(ids)) != expected_teams or any(tid is None for tid in ids):
        raise ValueError("Duplicate or missing ESPN team IDs")
    total = projected = 0
    missing = []
    for team in teams:
        roster = team.get("roster")
        entries = roster.get("entries") if isinstance(roster, dict) else None
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"Team {team['id']} has no roster entries")
        for entry in entries:
            player = (entry.get("playerPoolEntry") or {}).get("player") or {}
            total += 1
            if weekly_projection(player, week):
                projected += 1
            else:
                missing.append({"team_id": team["id"], "player_id": player.get("id", entry.get("playerId"))})
    # An absent projection for a particular player is allowed and recorded;
    # it is NOT interpreted as zero or a valid starter.
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(output)
    return {"week": week, "teams": len(teams), "roster_entries": total,
            "projected": projected, "missing": missing}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--league-id", type=int, default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-week", type=int, default=9)
    parser.add_argument("--end-week", type=int, default=14)
    parser.add_argument("--expected-teams", type=int, default=14)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()
    if not 1 <= args.start_week <= args.end_week <= 18:
        parser.error("Expected NFL weeks 1 through 18 in ascending order")
    session = build_session()
    for week in range(args.start_week, args.end_week + 1):
        path = args.data_root / "raw" / str(args.season) / "weeks" / f"{week:02d}" / "mRoster.json"
        try:
            report = fetch_week(session, args.league_id, args.season, week, path, args.expected_teams)
            print(json.dumps(report, sort_keys=True))
        except Exception as exc:
            print(json.dumps({"week": week, "status": "unavailable",
                              "error": f"{type(exc).__name__}: {str(exc)[:180]}"}))


if __name__ == "__main__":
    main()
