"""Extract week-specific ESPN player projections into optimal team lineup means.

Fail closed on absent or ambiguous projection data; never convert missing to zero.
"""
import json
from pathlib import Path

from scripts.analytics.optimal_lineup import optimize_lineup


def starter_slots(settings):
    counts = settings["settings"]["rosterSettings"]["lineupSlotCounts"]
    slots = []
    for raw_slot, raw_count in counts.items():
        slot, count = int(raw_slot), int(raw_count)
        if slot in (20, 21):  # bench / IR
            continue
        if count < 0:
            raise ValueError("Invalid ESPN lineup count")
        slots.extend([slot] * count)
    if not slots:
        raise ValueError("No ESPN starting slots found")
    return slots


def projection_for_week(player, week):
    stats = player.get("stats", [])
    matches = [s["appliedTotal"] for s in stats
               if isinstance(s, dict) and s.get("statSourceId") == 1
               and s.get("scoringPeriodId") == week
               and isinstance(s.get("appliedTotal"), (int, float))
               and not isinstance(s.get("appliedTotal"), bool)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one weekly ESPN projection, found {len(matches)}")
    return float(matches[0])


def roster_entries(payload):
    """Support mRoster team-level roster and mBoxscore matchup-side rosters."""
    teams = payload.get("teams", [])
    found = {}
    for team in teams:
        if "roster" in team and isinstance(team["roster"], dict):
            found[int(team["id"])] = team["roster"].get("entries", [])
    for matchup in payload.get("schedule", []):
        for side in ("home", "away"):
            participant = matchup.get(side) or {}
            if participant.get("teamId") is None:
                continue
            roster = participant.get("rosterForCurrentScoringPeriod")
            if isinstance(roster, dict) and "entries" in roster:
                found[int(participant["teamId"])] = roster["entries"]
    return found


def normalized_players(entries, week):
    players = []
    for entry in entries:
        pool = entry.get("playerPoolEntry") or {}
        player = pool.get("player") or {}
        pid = player.get("id", entry.get("playerId"))
        if pid is None:
            raise ValueError("Roster entry missing player ID")
        players.append({"player_id": int(pid),
                        "projection": projection_for_week(player, week),
                        "eligible_slots": [int(slot) for slot in player.get("eligibleSlots", [])],
                        "available": True})
    return players


def extract_weekly_means(data_root, season, weeks, team_ids):
    root = Path(data_root) / "raw" / str(season)
    settings = json.loads((root / "league" / "mSettings.json").read_text())
    slots = starter_slots(settings)
    means = {int(tid): {} for tid in team_ids}
    coverage = []
    for week in weeks:
        path = root / "weeks" / f"{week:02d}" / "mRoster.json"
        if not path.exists():
            coverage.append({"week": week, "status": "missing_file"})
            continue
        payload = json.loads(path.read_text())
        rosters = roster_entries(payload)
        successful = 0
        for tid in means:
            entries = rosters.get(tid)
            if not entries:
                continue
            try:
                means[tid][week] = optimize_lineup(normalized_players(entries, week), slots)["projected_points"]
                successful += 1
            except (ValueError, KeyError, TypeError):
                continue
        coverage.append({"week": week, "teams_with_valid_lineups": successful,
                         "teams_expected": len(means),
                         "status": "complete" if successful == len(means) else "incomplete"})
    return {"means": means, "coverage": coverage,
            "ready": all(row["status"] == "complete" for row in coverage)}
