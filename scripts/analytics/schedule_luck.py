"""Regular-season schedule difficulty and schedule-swap counterfactuals.

Only complete, finalized league weeks count. A schedule swap assigns the target
team's weekly score to the schedule owner's matchup slot; if the target team
was originally that owner's opponent, the owner becomes the opponent instead.
This avoids self-matches and preserves one matchup per week.
"""
from collections import defaultdict


def calculate_schedule_luck(season):
    teams = season["teams"]
    ids = {t["team_id"] for t in teams}
    if len(ids) != len(teams):
        raise ValueError("Duplicate team IDs")
    scores = defaultdict(dict)
    opponents = defaultdict(dict)
    for m in season["matchups"]:
        if m.get("stage") != "regular_season" or not m.get("decided"):
            continue
        w = m.get("matchup_period")
        a, b = m.get("home_team_id"), m.get("away_team_id")
        x, y = m.get("home_score"), m.get("away_score")
        if not isinstance(w, int) or isinstance(w, bool) or a not in ids or b not in ids or a == b:
            raise ValueError("Invalid regular-season matchup")
        if any(not isinstance(s, (int, float)) or isinstance(s, bool) for s in (x, y)):
            raise ValueError("Invalid finalized score")
        if a in scores[w] or b in scores[w]:
            raise ValueError("Duplicate team/week score")
        scores[w].update({a: x, b: y})
        opponents[w].update({a: b, b: a})

    eligible = [w for w in sorted(scores) if set(scores[w]) == ids]
    result = []
    for team in teams:
        tid = team["team_id"]
        actual = 0.0
        points_against = 0.0
        weekly_opponent_ranks = []
        swap = []
        for owner in teams:
            oid = owner["team_id"]
            equivalent_wins = 0.0
            for w in eligible:
                opponent = opponents[w][oid]
                # When swapping the target into the owner's slot, the owner
                # replaces the target in the opposing slot.
                if opponent == tid and oid != tid:
                    opponent = oid
                own_score = scores[w][tid]
                opposing_score = scores[w][opponent]
                equivalent_wins += (own_score > opposing_score) + 0.5 * (own_score == opposing_score)
                if oid == tid:
                    points_against += opposing_score
                    weekly_opponent_ranks.append(
                        1 + sum(score > opposing_score for score in scores[w].values()))
            swap.append({"schedule_team_id": oid, "schedule_team_name": owner["team_name"],
                         "wins": round(equivalent_wins, 4)})
            if oid == tid:
                actual = equivalent_wins
        values = [entry["wins"] for entry in swap]
        mean = sum(values) / len(values) if values else 0.0
        result.append({
            "team_id": tid, "team_name": team["team_name"], "weeks": len(eligible),
            "points_against": round(points_against, 2),
            "points_against_per_week": round(points_against / len(eligible), 2) if eligible else 0.0,
            "average_opponent_weekly_rank": round(sum(weekly_opponent_ranks) / len(eligible), 2) if eligible else None,
            "actual_wins": round(actual, 4),
            "average_schedule_wins": round(mean, 4),
            "schedule_luck": round(actual - mean, 4),
            "schedule_swap": swap,
        })
    return {"season": season["season"], "completed_weeks": eligible,
            "teams": sorted(result, key=lambda row: (-row["points_against_per_week"], row["team_name"]))}
