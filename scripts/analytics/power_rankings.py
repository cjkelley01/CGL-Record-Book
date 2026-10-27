"""Transparent, deterministic weekly CGL power rankings.

Strength is based on completed regular-season scoring only, not schedule luck.
Component weights: 40% points per week, 35% all-play win rate, 20% last-three
weekly scoring percentile, 5% consistency (lower scoring variability).
All four components are cross-team percentile ranks from 0 to 100.
"""
from collections import defaultdict
from statistics import pstdev


def _percentile(values, target, higher_is_better=True):
    if len(values) <= 1:
        return 50.0
    favorable = sum((v < target if higher_is_better else v > target) for v in values)
    ties = sum(v == target for v in values) - 1
    return 100.0 * (favorable + max(ties, 0) / 2) / (len(values) - 1)


def calculate_power_rankings(season):
    teams = season["teams"]
    ids = {team["team_id"] for team in teams}
    if len(ids) != len(teams):
        raise ValueError("Duplicate team IDs")
    weekly = defaultdict(dict)
    for m in season["matchups"]:
        if m.get("stage") != "regular_season" or not m.get("decided"):
            continue
        week = m.get("matchup_period")
        a, b = m.get("home_team_id"), m.get("away_team_id")
        x, y = m.get("home_score"), m.get("away_score")
        if not isinstance(week, int) or isinstance(week, bool) or a not in ids or b not in ids or a == b:
            raise ValueError("Invalid completed matchup")
        if any(not isinstance(s, (int, float)) or isinstance(s, bool) for s in (x, y)):
            raise ValueError("Invalid finalized score")
        if a in weekly[week] or b in weekly[week]:
            raise ValueError("Duplicate team/week score")
        weekly[week].update({a: x, b: y})
    eligible = [w for w in sorted(weekly) if set(weekly[w]) == ids]
    history = []
    previous = {}
    for week in eligible:
        included = [w for w in eligible if w <= week]
        raw = []
        for team in teams:
            tid = team["team_id"]
            scores = [weekly[w][tid] for w in included]
            allplay = sum(
                (scores[i] > weekly[w][opp]) + 0.5 * (scores[i] == weekly[w][opp])
                for i, w in enumerate(included) for opp in ids if opp != tid
            ) / (len(included) * (len(ids) - 1)) if len(ids) > 1 else 0.5
            recent = included[-3:]
            recent_pct = sum(
                (sum(weekly[w][tid] > v for oid, v in weekly[w].items() if oid != tid) +
                 0.5 * sum(weekly[w][tid] == v for oid, v in weekly[w].items() if oid != tid)) /
                (len(ids) - 1) if len(ids) > 1 else 0.5 for w in recent
            ) / len(recent)
            raw.append({"team_id": tid, "team_name": team["team_name"],
                        "points_per_week": sum(scores) / len(scores),
                        "all_play_rate": allplay, "recent_form": recent_pct,
                        "scoring_stddev": pstdev(scores)})
        for row in raw:
            components = {
                "scoring": _percentile([r["points_per_week"] for r in raw], row["points_per_week"]),
                "all_play": _percentile([r["all_play_rate"] for r in raw], row["all_play_rate"]),
                "recent": _percentile([r["recent_form"] for r in raw], row["recent_form"]),
                "consistency": _percentile([r["scoring_stddev"] for r in raw], row["scoring_stddev"], False),
            }
            row["components"] = {k: round(v, 2) for k, v in components.items()}
            row["power_score"] = round(.40 * components["scoring"] +
                                       .35 * components["all_play"] +
                                       .20 * components["recent"] +
                                       .05 * components["consistency"], 2)
            for key in ("points_per_week", "all_play_rate", "recent_form", "scoring_stddev"):
                row[key] = round(row[key], 4)
        ordered = sorted(raw, key=lambda r: (-r["power_score"], -r["points_per_week"], r["team_name"]))
        for index, row in enumerate(ordered, 1):
            row["rank"] = index
            row["rank_change"] = previous.get(row["team_id"], index) - index if previous else None
        previous = {row["team_id"]: row["rank"] for row in ordered}
        history.append({"week": week, "teams": ordered})
    return {"season": season["season"], "completed_weeks": eligible,
            "method": "Percentile ranks: 40% points/week, 35% all-play, 20% recent three-week form, 5% consistency",
            "weekly_rankings": history}
