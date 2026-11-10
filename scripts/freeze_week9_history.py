"""Create a Week-9-only historical snapshot from authenticated ESPN final scores.

Never edit the website's core_history.json; use an isolated report as simulator input.
"""
import argparse
import copy
import json
from pathlib import Path


def freeze_week9_history(history, espn):
    result = copy.deepcopy(history)
    season = next(s for s in result["seasons"] if s["season"] == 2026)
    regular = [m for m in season["matchups"] if m.get("stage") == "regular_season"]
    before = [m for m in regular if m["matchup_period"] < 9]
    week9 = [m for m in regular if m["matchup_period"] == 9]
    after = [m for m in regular if m["matchup_period"] > 9]
    if len(before) != 56 or not all(m["decided"] for m in before):
        raise ValueError("Expected all 56 regular-season games through Week 8 to be final")
    if len(week9) != 7 or len(after) != 35 or any(m["decided"] for m in after):
        raise ValueError("History must contain seven Week 9 games and 35 undecided Weeks 10-14 games")
    games = [m for m in espn.get("schedule", [])
             if int(m.get("matchupPeriodId", -1)) == 9]
    if len(games) != 7 or len({int(g["id"]) for g in games}) != 7:
        raise ValueError("ESPN Week 9 must contain seven uniquely identified matchups")
    lookup = {int(m["id"]): m for m in games}
    if set(lookup) != {int(m["matchup_id"]) for m in week9}:
        raise ValueError("ESPN Week 9 matchup IDs differ from frozen schedule")
    for existing in week9:
        source = lookup[existing["matchup_id"]]
        a, b = source.get("home") or {}, source.get("away") or {}
        if int(a.get("teamId", -1)) != existing["home_team_id"] or int(b.get("teamId", -1)) != existing["away_team_id"]:
            raise ValueError("ESPN Week 9 opponent identity mismatch")
        x, y = a.get("totalPoints"), b.get("totalPoints")
        if any(isinstance(p, bool) or not isinstance(p, (int, float)) or p <= 0 for p in (x, y)):
            raise ValueError("ESPN Week 9 score missing or nonpositive")
        winner = "HOME" if x > y else "AWAY" if y > x else "TIE"
        if source.get("winner") != winner:
            raise ValueError("ESPN Week 9 not finalized or winner/score mismatch")
        if existing["decided"] and (existing["home_score"] != x or existing["away_score"] != y):
            raise ValueError("Conflicting previously-final Week 9 scores")
        existing.update({"home_score": float(x), "away_score": float(y),
                         "winner": winner, "decided": True,
                         "margin": round(abs(x - y), 2),
                         "combined_score": round(x + y, 2),
                         "source": "data/raw/2026/league/mMatchupScore.json (Week 9 final)"})
    season["through_week"] = 9
    result["simulation_snapshot"] = {"as_of_week": 9, "source": "authenticated ESPN final Week 9 schedule",
                                     "future_results_excluded": True}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, default=Path("app/data/core_history.json"))
    parser.add_argument("--espn", type=Path, default=Path("data/raw/2026/league/mMatchupScore.json"))
    parser.add_argument("--output", type=Path, default=Path("data/reports/week9_history_snapshot.json"))
    args = parser.parse_args()
    snapshot = freeze_week9_history(json.loads(args.history.read_text()),
                                    json.loads(args.espn.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen Week 9 snapshot: {args.output}")


if __name__ == "__main__":
    main()
