"""Deterministic, regular-season all-play and expected-win statistics.

Input is the Record Book's normalized season object. Only finalized matchups
are eligible. A week is included only when every participating team has one
validated score, preventing partial/live weeks from biasing expected wins.
"""

from collections import defaultdict


def calculate_all_play(season):
    teams = season["teams"]
    ids = {team["team_id"] for team in teams}
    if len(ids) != len(teams):
        raise ValueError("Duplicate team IDs")
    weeks = defaultdict(dict)
    actual = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0})
    for matchup in season["matchups"]:
        if matchup.get("stage") != "regular_season" or not matchup.get("decided"):
            continue
        home, away = matchup.get("home_team_id"), matchup.get("away_team_id")
        hs, aws = matchup.get("home_score"), matchup.get("away_score")
        week = matchup.get("matchup_period")
        if home not in ids or away not in ids or home == away or not isinstance(week, int):
            raise ValueError("Invalid completed regular-season matchup")
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in (hs, aws)):
            raise ValueError("Completed matchup has invalid scores")
        if home in weeks[week] or away in weeks[week]:
            raise ValueError("Duplicate team/week score")
        weeks[week][home], weeks[week][away] = hs, aws
        if hs > aws:
            actual[home]["wins"] += 1
            actual[away]["losses"] += 1
        elif aws > hs:
            actual[away]["wins"] += 1
            actual[home]["losses"] += 1
        else:
            actual[home]["ties"] += 1
            actual[away]["ties"] += 1

    results = {team["team_id"]: {
        "team_id": team["team_id"], "team_name": team["team_name"],
        "weeks": 0, "all_play_wins": 0, "all_play_losses": 0,
        "all_play_ties": 0, "expected_wins": 0.0,
        "actual_win_equivalents": 0.0, "luck_differential": 0.0,
    } for team in teams}
    eligible = []
    for week, scores in sorted(weeks.items()):
        if set(scores) != ids:
            continue
        eligible.append(week)
        for team_id, points in scores.items():
            row = results[team_id]
            wins = sum(points > other for opponent, other in scores.items() if opponent != team_id)
            losses = sum(points < other for opponent, other in scores.items() if opponent != team_id)
            ties = len(ids) - 1 - wins - losses
            row["weeks"] += 1
            row["all_play_wins"] += wins
            row["all_play_losses"] += losses
            row["all_play_ties"] += ties
            row["expected_wins"] += (wins + 0.5 * ties) / (len(ids) - 1)

    for team_id, row in results.items():
        # Use only the same fully completed weeks as expected wins.
        qualified = [m for m in season["matchups"] if
                     m.get("stage") == "regular_season" and m.get("decided") and
                     m.get("matchup_period") in eligible and
                     team_id in (m.get("home_team_id"), m.get("away_team_id"))]
        wins = ties = 0
        for m in qualified:
            home = m["home_team_id"] == team_id
            own = m["home_score"] if home else m["away_score"]
            other = m["away_score"] if home else m["home_score"]
            wins += own > other
            ties += own == other
        row["actual_win_equivalents"] = wins + 0.5 * ties
        row["expected_wins"] = round(row["expected_wins"], 4)
        row["luck_differential"] = round(row["actual_win_equivalents"] - row["expected_wins"], 4)
    return {"season": season["season"], "completed_weeks": eligible,
            "teams": sorted(results.values(), key=lambda r: (-r["expected_wins"], r["team_name"]))}
