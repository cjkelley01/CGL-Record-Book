"""Pure, reproducible regular-season Monte Carlo simulator.

Inputs: normalized CGL season and explicit team-by-week means. This module
does not invent ESPN projections. A caller must validate future roster data
before passing roster-aware or blended means.
"""
import random
from collections import defaultdict


def simulate_regular_season(season, weekly_means, *, simulations=10000, seed=2026,
                            standard_deviation=18.0):
    if simulations <= 0 or standard_deviation <= 0:
        raise ValueError("Simulations and standard deviation must be positive")
    teams = season["teams"]
    ids = {t["team_id"] for t in teams}
    if len(ids) != len(teams):
        raise ValueError("Duplicate team IDs")
    regular = [m for m in season["matchups"] if m.get("stage") == "regular_season"]
    future = [m for m in regular if not m.get("decided")]
    complete = [m for m in regular if m.get("decided")]
    initial_wins = defaultdict(float)
    initial_points = defaultdict(float)
    for m in complete:
        a, b = m["home_team_id"], m["away_team_id"]
        x, y = m["home_score"], m["away_score"]
        if a not in ids or b not in ids or x is None or y is None:
            raise ValueError("Incomplete decided matchup")
        initial_wins[a] += (x > y) + 0.5 * (x == y)
        initial_wins[b] += (y > x) + 0.5 * (x == y)
        initial_points[a] += x
        initial_points[b] += y
    for m in future:
        w = m["matchup_period"]
        for tid in (m["home_team_id"], m["away_team_id"]):
            if tid not in ids or tid not in weekly_means or w not in weekly_means[tid]:
                raise ValueError(f"Missing validated future projection for team {tid}, week {w}")
            if not isinstance(weekly_means[tid][w], (int, float)):
                raise ValueError("Projection must be numeric")
    rng = random.Random(seed)
    stats = {tid: {"playoffs": 0, "bye": 0, "seed_sum": 0, "wins_sum": 0.0,
                   "seed_counts": defaultdict(int)} for tid in ids}
    for _ in range(simulations):
        wins = initial_wins.copy()
        points = initial_points.copy()
        for m in future:
            a, b, w = m["home_team_id"], m["away_team_id"], m["matchup_period"]
            x = max(0.0, rng.gauss(weekly_means[a][w], standard_deviation))
            y = max(0.0, rng.gauss(weekly_means[b][w], standard_deviation))
            wins[a] += x > y
            wins[b] += y > x
            points[a] += x
            points[b] += y
        ordered = sorted(ids, key=lambda tid: (-wins[tid], -points[tid], tid))
        for rank, tid in enumerate(ordered, 1):
            s = stats[tid]
            s["playoffs"] += rank <= 6
            s["bye"] += rank <= 2
            s["seed_sum"] += rank
            s["wins_sum"] += wins[tid]
            s["seed_counts"][rank] += 1
    return {"season": season["season"], "simulations": simulations, "seed": seed,
            "model": "explicit_weekly_means_gaussian",
            "assumptions": {"score_standard_deviation": standard_deviation,
                            "tiebreak": "regular-season points for",
                            "roster_projections_verified": False},
            "teams": [{
                "team_id": t["team_id"], "team_name": t["team_name"],
                "playoff_probability": round(stats[t["team_id"]]["playoffs"] / simulations, 4),
                "bye_probability": round(stats[t["team_id"]]["bye"] / simulations, 4),
                "expected_seed": round(stats[t["team_id"]]["seed_sum"] / simulations, 2),
                "expected_wins": round(stats[t["team_id"]]["wins_sum"] / simulations, 2),
                "seed_probabilities": {str(rank): round(count / simulations, 4)
                    for rank, count in sorted(stats[t["team_id"]]["seed_counts"].items())},
            } for t in teams]}
