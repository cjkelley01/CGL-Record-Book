"""Weekly CGL playoff and championship forecasts.

Historical estimates use completed 2026 scoring only. Roster estimates require
verified ESPN week-specific legal lineups. Unavailable models are not fabricated.
"""
import argparse
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.analytics.espn_projections import extract_weekly_means


def completed_scores(season):
    scores = defaultdict(list)
    for game in season["matchups"]:
        if game.get("stage") != "regular_season" or not game.get("decided"):
            continue
        for side in ("home", "away"):
            tid, value = game.get(side + "_team_id"), game.get(side + "_score")
            if tid is not None and isinstance(value, (int, float)):
                scores[int(tid)].append(float(value))
    return scores


def historical_means(season, weeks):
    scores = completed_scores(season)
    ids = [int(t["team_id"]) for t in season["teams"]]
    if any(not scores.get(tid) for tid in ids):
        return None
    return {tid: {week: sum(scores[tid]) / len(scores[tid]) for week in weeks}
            for tid in ids}


def blended_means(historical, roster, historical_weight=0.4):
    if historical is None or roster is None:
        return None
    return {tid: {week: historical_weight * historical[tid][week]
                  + (1 - historical_weight) * roster[tid][week]
                  for week in historical[tid]} for tid in historical}


def simulate(season, means, *, trials=10000, seed=2026, deviation=18.0):
    if trials < 1 or deviation <= 0:
        raise ValueError("Invalid simulation settings")
    ids = [int(t["team_id"]) for t in season["teams"]]
    if len(ids) != len(set(ids)) or len(ids) < 6:
        raise ValueError("Expected six playoff places and unique team IDs")
    regular = [m for m in season["matchups"] if m.get("stage") == "regular_season"]
    completed = [m for m in regular if m.get("decided")]
    future = [m for m in regular if not m.get("decided")]
    wins = defaultdict(float)
    points = defaultdict(float)
    for game in completed:
        a, b = int(game["home_team_id"]), int(game["away_team_id"])
        x, y = game["home_score"], game["away_score"]
        if x is None or y is None:
            raise ValueError("Decided game missing scores")
        wins[a] += (x > y) + .5 * (x == y)
        wins[b] += (y > x) + .5 * (x == y)
        points[a] += x
        points[b] += y
    weeks = {int(m["matchup_period"]) for m in future} | {15, 16, 17, 18}
    for tid in ids:
        for week in weeks:
            if not math.isfinite(means.get(tid, {}).get(week, float("nan"))):
                raise ValueError(f"Missing score estimate for team {tid}, week {week}")
    stats = {tid: {"playoffs": 0, "bye": 0, "champion": 0, "finalist": 0,
                   "wins": 0.0, "seed": 0.0, "seed_counts": defaultdict(int)} for tid in ids}
    rng = random.Random(seed)
    def score(tid, week):
        return max(0.0, rng.gauss(means[tid][week], deviation))
    for _ in range(trials):
        w, p = wins.copy(), points.copy()
        for game in future:
            a, b, week = int(game["home_team_id"]), int(game["away_team_id"]), int(game["matchup_period"])
            x, y = score(a, week), score(b, week)
            w[a] += (x > y) + .5 * (x == y)
            w[b] += (y > x) + .5 * (x == y)
            p[a] += x
            p[b] += y
        ordered = sorted(ids, key=lambda tid: (-w[tid], -p[tid], tid))
        seeded = {tid: i + 1 for i, tid in enumerate(ordered)}
        for tid in ids:
            rank = seeded[tid]
            s = stats[tid]
            s["playoffs"] += rank <= 6
            s["bye"] += rank <= 2
            s["seed"] += rank
            s["wins"] += w[tid]
            s["seed_counts"][rank] += 1
        def winner(a, b, week):
            x, y = score(a, week), score(b, week)
            return a if x > y or (x == y and seeded[a] < seeded[b]) else b
        first = [winner(ordered[2], ordered[5], 15),
                 winner(ordered[3], ordered[4], 15)]
        first.sort(key=lambda tid: seeded[tid])
        semi = [winner(ordered[0], first[1], 16),
                winner(ordered[1], first[0], 16)]
        for tid in semi:
            stats[tid]["finalist"] += 1
        a, b = semi
        ax = score(a, 17) + score(a, 18)
        bx = score(b, 17) + score(b, 18)
        champ = a if ax > bx or (ax == bx and seeded[a] < seeded[b]) else b
        stats[champ]["champion"] += 1
    return {"simulations": trials, "seed": seed,
            "assumptions": {"weekly_score_sd": deviation, "tiebreak": "points_for",
                            "bracket": "6 teams; 1-2 byes; W15 quarterfinal, W16 semifinal, W17-18 final"},
            "teams": [{"team_id": tid, "team_name": next(t["team_name"] for t in season["teams"] if int(t["team_id"]) == tid),
                       "playoff_probability": round(stats[tid]["playoffs"] / trials, 4),
                       "bye_probability": round(stats[tid]["bye"] / trials, 4),
                       "championship_probability": round(stats[tid]["champion"] / trials, 4),
                       "final_probability": round(stats[tid]["finalist"] / trials, 4),
                       "expected_seed": round(stats[tid]["seed"] / trials, 2),
                       "expected_wins": round(stats[tid]["wins"] / trials, 2),
                       "seed_probabilities": {str(k): round(v / trials, 4)
                                              for k, v in sorted(stats[tid]["seed_counts"].items())}}
                      for tid in ids]}


def build_forecast(season, data_root, *, trials=10000):
    future = sorted({int(m["matchup_period"]) for m in season["matchups"]
                     if m.get("stage") == "regular_season" and not m.get("decided")})
    weeks = sorted(set(future) | {15, 16, 17, 18})
    ids = [int(t["team_id"]) for t in season["teams"]]
    history = historical_means(season, weeks)
    roster_result = extract_weekly_means(data_root, season["season"], weeks, ids)
    roster = roster_result["means"] if roster_result["ready"] else None
    models = {}
    for name, means in (("historical", history), ("roster_aware", roster),
                        ("blended", blended_means(history, roster))):
        if means is None:
            models[name] = {"status": "unavailable", "reason": (
                "Not all teams have completed games" if name == "historical"
                else "Incomplete legal ESPN weekly lineup projections" if name == "roster_aware"
                else "Requires both historical and roster-aware inputs")}
        else:
            models[name] = {"status": "available", **simulate(season, means, trials=trials)}
    return {"season": season["season"], "generated_at": datetime.now(timezone.utc).isoformat(),
            "completed_through_week": max((int(m["matchup_period"]) for m in season["matchups"]
                if m.get("stage") == "regular_season" and m.get("decided")), default=0),
            "projection_coverage": roster_result["coverage"], "models": models}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--history", type=Path, default=Path("app/data/core_history.json"))
    parser.add_argument("--output", type=Path, default=Path("app/data/playoff_forecast.json"))
    parser.add_argument("--trials", type=int, default=10000)
    args = parser.parse_args()
    history = json.loads(args.history.read_text())
    season = next(s for s in history["seasons"] if s["season"] == 2026)
    result = build_forecast(season, args.data_root, trials=args.trials)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    snapshot = Path("data/forecasts") / f"2026-week-{result['completed_through_week']:02d}.json"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"week": result["completed_through_week"],
                      "models": {k: v["status"] for k, v in result["models"].items()}}, indent=2))


if __name__ == "__main__":
    main()
