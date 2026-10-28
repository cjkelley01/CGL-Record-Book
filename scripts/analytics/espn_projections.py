"""Extract week-specific ESPN player projections into optimal team lineup means.

Fail closed on absent or ambiguous projection data; never convert missing to zero.
"""
import json
import math
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
    value = float(matches[0])
    if not math.isfinite(value):
        raise ValueError("Non-finite projection")
    return value


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


def is_playable(player, week, playing_teams=None):
    """ESPN projected schedule: bye/inactive players must not fill a starter slot.

    ESPN uses proTeamSchedules with proTeamId and scoringPeriodId; when schedule
    data is missing, zero projections cannot establish a playable starter.
    """
    if playing_teams is not None:
        pro_team = player.get("proTeamId")
        if pro_team is None or int(pro_team) not in playing_teams:
            return False
    if player.get("onBye") is True or player.get("byeWeek") == week:
        return False
    stats = player.get("stats") or []
    projected = [s for s in stats if isinstance(s, dict) and
                 s.get("statSourceId") == 1 and s.get("scoringPeriodId") == week]
    if not projected:
        return False
    # A positive projection is strong evidence of an actual game; zero alone
    # is not evidence, particularly for D/STs on bye.
    return any(isinstance(s.get("appliedTotal"), (int, float)) and
               s["appliedTotal"] > 0 for s in projected)


def normalized_players(entries, week, *, skip_missing=False, playing_teams=None):
    players = []
    for entry in entries:
        pool = entry.get("playerPoolEntry") or {}
        player = pool.get("player") or {}
        pid = player.get("id", entry.get("playerId"))
        if pid is None:
            raise ValueError("Roster entry missing player ID")
        try:
            if not is_playable(player, week, playing_teams):
                raise ValueError("Player has no verified playable projection this week")
            projection = projection_for_week(player, week)
        except ValueError:
            if skip_missing:
                continue  # Bye/injury/unprojected player cannot be selected.
            raise
        players.append({"player_id": int(pid),
                        "projection": projection,
                        "eligible_slots": [int(slot) for slot in player.get("eligibleSlots", [])],
                        "available": True})
    return players


def waiver_replacements(pool, week, rostered_ids, slots, playing_teams=None):
    """Conservative slot-specific estimates from ESPN-confirmed unrostered players.

    Use the average projection of the three highest eligible available options
    per slot, rather than assuming the best player is guaranteed.
    """
    if not isinstance(pool, list):
        return []
    eligible = []
    for entry in pool:
        if not isinstance(entry, dict):
            continue
        player = entry.get("player") or (entry.get("playerPoolEntry") or {}).get("player") or {}
        pid = player.get("id")
        # Explicit ESPN ownership/status confirmation is mandatory.
        status = entry.get("status") or (entry.get("playerPoolEntry") or {}).get("status")
        owner = entry.get("onTeamId", (entry.get("playerPoolEntry") or {}).get("onTeamId"))
        if status not in ("FREEAGENT", "WAIVERS") or owner not in (0, None, -1):
            continue
        if pid is None or int(pid) in rostered_ids:
            continue
        try:
            if not is_playable(player, week):
                continue
            points = projection_for_week(player, week)
        except ValueError:
            continue
        if points < 0:
            continue
        eligible.append({"player_id": int(pid), "projection": points,
                         "eligible_slots": [int(s) for s in player.get("eligibleSlots", [])]})
    selected = []
    for slot in sorted(set(slots)):
        options = sorted((p for p in eligible if slot in p["eligible_slots"]),
                         key=lambda p: (-p["projection"], p["player_id"]))
        if len(options) < 3:
            continue
        top_three = options[:3]
        estimate = sum(p["projection"] for p in top_three) / 3
        # Synthetic projection estimate, not a claimed player acquisition.
        for occurrence in range(slots.count(slot)):
            selected.append({"player_id": -(1000000 + slot * 100 + occurrence), "projection": estimate,
                             "eligible_slots": [slot]})
    return selected


def extract_weekly_means(data_root, season, weeks, team_ids):
    root = Path(data_root) / "raw" / str(season)
    settings = json.loads((root / "league" / "mSettings.json").read_text())
    slots = starter_slots(settings)
    means = {int(tid): {} for tid in team_ids}
    coverage = []
    schedule_path = root / "nfl_schedule.json"
    schedule = json.loads(schedule_path.read_text()) if schedule_path.exists() else {}
    for week in weeks:
        playing = set(schedule.get(str(week), []))
        if not 26 <= len(playing) <= 32:
            coverage.append({"week": week, "status": "missing_verified_nfl_schedule",
                             "teams_with_valid_lineups": 0, "teams_expected": len(means)})
            continue
        path = root / "weeks" / f"{week:02d}" / "mRoster.json"
        if not path.exists():
            coverage.append({"week": week, "status": "missing_file"})
            continue
        payload = json.loads(path.read_text())
        rosters = roster_entries(payload)
        successful = 0
        replacements_used = 0
        failed_teams = []
        replacement_teams = []
        rostered_ids = {int((e.get("playerPoolEntry") or {}).get("player", {}).get("id") or e.get("playerId"))
                        for entries in rosters.values() for e in entries
                        if (e.get("playerPoolEntry") or {}).get("player", {}).get("id") or e.get("playerId")}
        pool_path = root / "weeks" / f"{week:02d}" / "free_agents.json"
        pool = json.loads(pool_path.read_text()) if pool_path.exists() else None
        fallback = waiver_replacements(pool, week, rostered_ids, slots, playing)
        for tid in means:
            entries = rosters.get(tid)
            if not entries:
                continue
            try:
                roster_players = normalized_players(entries, week, skip_missing=True, playing_teams=playing)
                try:
                    optimized = optimize_lineup(roster_players, slots)
                except ValueError:
                    if not fallback:
                        raise
                    optimized = optimize_lineup(roster_players + fallback, slots)
                    replacements_used += 1
                    replacement_teams.append(tid)
                means[tid][week] = optimized["projected_points"]
                successful += 1
            except (ValueError, KeyError, TypeError) as exc:
                failed_teams.append({"team_id": tid, "reason": str(exc)[:150]})
                continue
        coverage.append({"week": week, "teams_using_waiver_replacements": replacements_used,
                         "waiver_pool_verified": pool is not None,
                         "teams_requiring_replacements": replacement_teams,
                         "teams_without_valid_lineups": failed_teams,
                         "teams_with_valid_lineups": successful,
                         "teams_expected": len(means),
                         "status": "complete" if successful == len(means) else "incomplete"})
    return {"means": means, "coverage": coverage,
            "ready": all(row["status"] == "complete" for row in coverage)}
