"""Cutoff-only historical roster-aware team estimates.

Historical mRoster records are treated as retrospective roster evidence, not
timestamp-verified snapshots. Only completed *earlier* player actuals are
eligible to estimate scores. Future projections and future player outcomes
are never consumed.
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from scripts.analytics.optimal_lineup import optimize_lineup

NON_STARTERS = {20, 21}


def load_player_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _slots(raw):
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
        return [int(x) for x in values] if isinstance(values, list) else []
    except (TypeError, ValueError):
        return []


def cutoff_lineup_estimates(rows, season, cutoff, team_ids, *, min_games=2):
    """Return team estimates and coverage; fail closed for incomplete lineups.

    For each player, use only actual points from weeks strictly before cutoff.
    Roster membership and starter slots come from cutoff week's roster query.
    The resulting fixed estimate is carried forward, NOT a future-week lineup.
    """
    past = defaultdict(list)
    current = defaultdict(list)
    for row in rows:
        if int(row["season"]) != season:
            continue
        week = int(row["week"])
        tid = int(row["team_id"])
        pid_raw = row.get("player_id")
        if not pid_raw:
            continue
        pid = int(pid_raw)
        if week < cutoff:
            value = _number(row.get("actual"))
            if value is not None and row.get("actual_records", "1") in ("1", 1):
                past[pid].append((week, value))
        elif week == cutoff:
            current[tid].append(row)
    estimates = {}
    coverage = {"season": season, "cutoff": cutoff, "teams_expected": len(team_ids),
                "teams_valid": 0, "missing_teams": [], "players_without_history": 0,
                "source": "retrospective cutoff-week roster; strictly earlier player actuals",
                "historical_future_projection_verified": False,
                "future_byes_and_injuries_modeled": False,
                "waiver_replacements_modeled": False}
    for tid in team_ids:
        entries = current.get(tid, [])
        slots = [int(r["lineup_slot_id"]) for r in entries
                 if r.get("lineup_slot_id") not in (None, "")
                 and int(r["lineup_slot_id"]) not in NON_STARTERS]
        players = []
        seen = set()
        for row in entries:
            pid = int(row["player_id"])
            if pid in seen:
                continue
            seen.add(pid)
            history = past.get(pid, [])
            # Historical actuals are not necessarily proof of playing in a
            # particular future week; this is a scoring-capacity proxy only.
            if len(history) < min_games:
                coverage["players_without_history"] += 1
                continue
            eligible = _slots(row.get("eligible_slots"))
            if not eligible:
                continue
            players.append({"player_id": pid,
                            "projection": sum(v for _, v in history) / len(history),
                            "eligible_slots": eligible})
        try:
            if not slots:
                raise ValueError("No observed starting slots")
            estimates[tid] = optimize_lineup(players, slots)["projected_points"]
        except ValueError:
            coverage["missing_teams"].append(tid)
    coverage["teams_valid"] = len(estimates)
    return (estimates if len(estimates) == len(team_ids) else None), coverage
