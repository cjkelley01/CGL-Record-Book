#!/usr/bin/env python3
"""Normalize preserved ESPN responses into the CGL historical record book."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


MANAGERS = {
    "charley_k": "Charley K.", "quy_h": "Quy H.", "mike_k": "Mike K.",
    "robin_h": "Robin H.", "jj_k": "JJ K.", "alex_h": "Alex H.",
    "tony_r": "Tony R.", "kelley_h": "Kelley H.", "susan_h": "Susan H.",
    "charley_b": "Charley B.", "ed_b": "Ed B.", "carolyn_b": "Carolyn B.",
    "timmy_k": "Timmy K.", "aaron_t": "Aaron T.", "emma_t": "Emma T.",
    "joseph_e": "Joseph E.", "airel_g": "Airel G.",
    "kaitlyn_k": "Kaitlyn K.", "burke_k": "Burke K.",
}

CURRENT_TEAM_NAME_MANAGERS = {
    "charley s angels": ["charley_k"], "kinda mid": ["aaron_t"],
    "mike s magic": ["mike_k"], "all the way to the em zone": ["emma_t"],
    "no refills": ["jj_k"], "flux capacitors": ["tony_r"],
    "big joe": ["joseph_e"], "sos": ["susan_h"],
    "cb s bulls": ["charley_b"], "ed s plus 1 team": ["ed_b", "carolyn_b"],
    "timberwolves": ["timmy_k"], "cardiac": ["airel_g"],
    "kaitlyn": ["kaitlyn_k"], "bk": ["burke_k"],
}

# Team IDs can be reused when league membership changes, so identity is mapped
# by season and team ID. Team names remain season-specific aliases.
TEAM_SEASON_MANAGERS = {
    (2024, 1): ["charley_k"], (2024, 2): ["quy_h"],
    (2024, 3): ["mike_k"], (2024, 4): ["robin_h"],
    (2024, 5): ["jj_k"], (2024, 8): ["alex_h"],
    (2024, 9): ["tony_r"], (2024, 10): ["kelley_h"],
    (2024, 13): ["susan_h"], (2024, 14): ["charley_b"],
    (2024, 17): ["ed_b", "carolyn_b"], (2024, 18): ["timmy_k"],
    (2025, 1): ["charley_k"], (2025, 2): ["aaron_t"],
    (2025, 3): ["mike_k"], (2025, 4): ["emma_t"],
    (2025, 5): ["jj_k"], (2025, 8): ["alex_h"],
    (2025, 9): ["tony_r"], (2025, 10): ["joseph_e"],
    (2025, 13): ["susan_h"], (2025, 14): ["charley_b"],
    (2025, 17): ["ed_b", "carolyn_b"], (2025, 18): ["timmy_k"],
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}. Run scripts/discover_espn_history.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_name(value: str) -> str:
    return " ".join("".join(char.lower() if char.isalnum() else " " for char in value).split())


def manager_ids(season: int, team_id: int, team_name: str) -> list[str]:
    mapped = TEAM_SEASON_MANAGERS.get((season, team_id))
    if mapped:
        return mapped
    if season >= 2026:
        normalized = normalized_name(team_name)
        for fragment, ids in CURRENT_TEAM_NAME_MANAGERS.items():
            if normalized == fragment or normalized.startswith(f"{fragment} ") or (len(fragment) > 3 and fragment in normalized):
                return ids
    raise ValueError(f"No manager mapping for {season} team {team_id}: {team_name!r}")


def manager_names(ids: list[str]) -> list[str]:
    return [MANAGERS[manager_id] for manager_id in ids]


def side_score(side: dict[str, Any] | None) -> float | None:
    value = side.get("totalPoints") if side else None
    return float(value) if value is not None else None


def matchup_stage(period: int, regular_periods: int, tier: str | None) -> str:
    if period <= regular_periods:
        return "regular_season"
    if tier == "WINNERS_BRACKET":
        return "championship_playoffs"
    if tier in {"WINNERS_CONSOLATION_LADDER", "LOSERS_CONSOLATION_LADDER"}:
        return "consolation"
    return "postseason_other"


def normalize_season(data_root: Path, season: int) -> dict[str, Any]:
    league = data_root / "raw" / str(season) / "league"
    settings_payload = read_json(league / "mSettings.json")
    teams_payload = read_json(league / "mTeam.json")
    matchup_payload = read_json(league / "mMatchupScore.json")
    draft_payload = read_json(league / "mDraftDetail.json")
    schedule_settings = settings_payload["settings"]["scheduleSettings"]
    regular_periods = int(schedule_settings["matchupPeriodCount"])

    teams, team_lookup = [], {}
    for team in teams_payload.get("teams", []):
        team_id = int(team["id"])
        team_name = (team.get("name") or team.get("abbrev") or f"Team {team_id}").strip()
        ids = manager_ids(season, team_id, team_name)
        overall = team.get("record", {}).get("overall", {})
        normalized = {
            "season": season, "team_id": team_id, "team_season_id": f"{season}:{team_id}",
            "team_name": team_name,
            "abbreviation": team.get("abbrev"), "manager_ids": ids,
            "manager_names": manager_names(ids), "logo": team.get("logo"),
            "regular_season": {key: value for key, value in {
                "wins": int(overall.get("wins", 0)), "losses": int(overall.get("losses", 0)),
                "ties": int(overall.get("ties", 0)), "points_for": float(overall.get("pointsFor", 0)),
                "points_against": float(overall.get("pointsAgainst", 0)),
            }.items()},
            "playoff_seed": team.get("playoffSeed"), "final_rank": team.get("rankCalculatedFinal"),
            "activity_totals": team.get("transactionCounter", {}),
            "source": f"data/raw/{season}/league/mTeam.json",
        }
        teams.append(normalized)
        team_lookup[team_id] = normalized

    matchups, weekly_scores = [], []
    for matchup in matchup_payload.get("schedule", []):
        period, tier = int(matchup["matchupPeriodId"]), matchup.get("playoffTierType")
        stage = matchup_stage(period, regular_periods, tier)
        home, away = matchup.get("home"), matchup.get("away")
        home_id = int(home["teamId"]) if home else None
        away_id = int(away["teamId"]) if away else None
        home_score, away_score = side_score(home), side_score(away)
        decided = home_id is not None and away_id is not None and matchup.get("winner") in {"HOME", "AWAY", "TIE"}
        scoring_periods = sorted({int(p) for side in (home, away) if side for p in side.get("pointsByScoringPeriod", {})})
        row = {
            "season": season, "matchup_id": int(matchup["id"]), "matchup_key": f"{season}:{matchup['id']}",
            "matchup_period": period, "scoring_periods": scoring_periods,
            "is_multiweek_series": len(scoring_periods) > 1, "stage": stage, "playoff_tier": tier,
            "playoff_round": period - regular_periods if period > regular_periods else None,
            "home_team_id": home_id, "home_team_name": team_lookup.get(home_id, {}).get("team_name"),
            "home_manager_ids": team_lookup.get(home_id, {}).get("manager_ids", []),
            "home_manager_names": team_lookup.get(home_id, {}).get("manager_names", []),
            "home_score": home_score, "away_team_id": away_id,
            "away_team_name": team_lookup.get(away_id, {}).get("team_name"),
            "away_manager_ids": team_lookup.get(away_id, {}).get("manager_ids", []),
            "away_manager_names": team_lookup.get(away_id, {}).get("manager_names", []),
            "away_score": away_score, "winner": matchup.get("winner"), "decided": decided,
            "margin": round(abs(home_score-away_score), 2) if decided and home_score is not None and away_score is not None else None,
            "combined_score": round(home_score+away_score, 2) if home_score is not None and away_score is not None else None,
            "source": f"data/raw/{season}/league/mMatchupScore.json",
        }
        matchups.append(row)
        for side_name, side in (("home", home), ("away", away)):
            if not side:
                continue
            team_id = int(side["teamId"])
            opponent_id = away_id if side_name == "home" else home_id
            for scoring_period, points in side.get("pointsByScoringPeriod", {}).items():
                weekly_scores.append({
                    "season": season, "scoring_period": int(scoring_period), "matchup_period": period,
                    "stage": stage, "playoff_tier": tier, "matchup_id": int(matchup["id"]),
                    "team_id": team_id, "team_name": team_lookup[team_id]["team_name"],
                    "manager_ids": team_lookup[team_id]["manager_ids"], "manager_names": team_lookup[team_id]["manager_names"],
                    "opponent_team_id": opponent_id, "opponent_team_name": team_lookup.get(opponent_id, {}).get("team_name"),
                    "points": float(points), "source": f"data/raw/{season}/league/mMatchupScore.json",
                })

    picks = []
    for pick in draft_payload.get("draftDetail", {}).get("picks", []):
        team_id = int(pick["teamId"])
        picks.append({
            "season": season, "overall_pick": int(pick["overallPickNumber"]), "round": int(pick["roundId"]),
            "round_pick": int(pick["roundPickNumber"]), "team_id": team_id,
            "team_name": team_lookup[team_id]["team_name"], "manager_ids": team_lookup[team_id]["manager_ids"],
            "manager_names": team_lookup[team_id]["manager_names"], "player_id": int(pick["playerId"]),
            "lineup_slot_id": pick.get("lineupSlotId"), "keeper": bool(pick.get("keeper", False)),
            "auto_draft_type_id": pick.get("autoDraftTypeId"), "source": f"data/raw/{season}/league/mDraftDetail.json",
        })

    season_complete = any(completed(matchup) and matchup["stage"] == "championship_playoffs" and matchup["is_multiweek_series"] for matchup in matchups)
    decided_periods = [period for matchup in matchups if completed(matchup) for period in matchup["scoring_periods"]]
    return {
        "season": season, "league_id": settings_payload["id"],
        "is_complete": season_complete,
        "through_week": max(decided_periods, default=0),
        "settings": {"team_count": len(teams), "regular_season_matchup_periods": regular_periods,
                     "playoff_team_count": schedule_settings.get("playoffTeamCount"),
                     "playoff_round_lengths": schedule_settings.get("playoffMatchupPeriodLengthByRound", {}),
                     "playoff_reseed": schedule_settings.get("playoffReseed"),
                     "playoff_seeding_rule": schedule_settings.get("playoffSeedingRule")},
        "teams": sorted(teams, key=lambda x: x["team_id"]),
        "matchups": sorted(matchups, key=lambda x: x["matchup_id"]),
        "weekly_scores": sorted(weekly_scores, key=lambda x: (x["scoring_period"], x["team_id"], x["matchup_id"])),
        "draft_picks": sorted(picks, key=lambda x: x["overall_pick"]),
    }


def completed(matchup: dict[str, Any]) -> bool:
    return bool(matchup["decided"] and matchup["home_team_id"] is not None and matchup["away_team_id"] is not None
                and matchup["home_score"] is not None and matchup["away_score"] is not None)


def result_for(matchup: dict[str, Any], side: str) -> str:
    if matchup["winner"] == "TIE": return "T"
    return "W" if matchup["winner"] == side.upper() else "L"


def matchup_label(m: dict[str, Any]) -> dict[str, Any]:
    return {key: m[key] for key in ("season", "matchup_period", "scoring_periods", "stage",
            "home_team_name", "home_manager_names", "home_score", "away_team_name",
            "away_manager_names", "away_score", "margin", "combined_score")}


def build_manager_history(seasons: list[dict[str, Any]]) -> dict[str, Any]:
    stats = {mid: {"manager_id": mid, "manager_name": name, "seasons": 0, "wins": 0, "losses": 0,
                    "ties": 0, "points_for": 0.0, "points_against": 0.0, "playoff_appearances": 0,
                    "championships": 0, "runner_up_finishes": 0, "team_names": []}
             for mid, name in MANAGERS.items()}
    aliases = defaultdict(list)
    for season in seasons:
        playoff_count = season["settings"]["playoff_team_count"]
        for team in season["teams"]:
            for mid in team["manager_ids"]:
                row, record = stats[mid], team["regular_season"]
                row["seasons"] += 1
                for key in ("wins", "losses", "ties", "points_for", "points_against"): row[key] += record[key]
                if season["is_complete"]:
                    row["playoff_appearances"] += int(team["playoff_seed"] is not None and team["playoff_seed"] <= playoff_count)
                    row["championships"] += int(team["final_rank"] == 1)
                    row["runner_up_finishes"] += int(team["final_rank"] == 2)
                aliases[mid].append({"season": season["season"], "team_id": team["team_id"], "team_name": team["team_name"]})
    for mid, row in stats.items():
        games = row["wins"] + row["losses"] + row["ties"]
        row["winning_percentage"] = round((row["wins"] + .5 * row["ties"]) / games, 4) if games else None
        row["points_for"], row["points_against"] = round(row["points_for"], 2), round(row["points_against"], 2)
        row["team_names"] = aliases[mid]
    active = [row for row in stats.values() if row["seasons"]]
    return {"standings": sorted(active, key=lambda r: (
                r["winning_percentage"] is None,
                -(r["winning_percentage"] or 0),
                -r["wins"],
                -r["points_for"],
                r["manager_name"],
            )),
            "team_name_history": {mid: aliases[mid] for mid in aliases}}


def build_head_to_head(seasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = {}
    for season in seasons:
        for m in season["matchups"]:
            if not completed(m) or m["stage"] != "regular_season": continue
            for home_mid in m["home_manager_ids"]:
                for away_mid in m["away_manager_ids"]:
                    ids = tuple(sorted((home_mid, away_mid)))
                    row = pairs.setdefault(ids, {"manager_1_id": ids[0], "manager_1_name": MANAGERS[ids[0]],
                        "manager_2_id": ids[1], "manager_2_name": MANAGERS[ids[1]], "manager_1_wins": 0,
                        "manager_2_wins": 0, "ties": 0, "games": 0})
                    row["games"] += 1
                    if m["winner"] == "TIE": row["ties"] += 1
                    else:
                        winner = home_mid if m["winner"] == "HOME" else away_mid
                        row["manager_1_wins" if winner == ids[0] else "manager_2_wins"] += 1
    return sorted(pairs.values(), key=lambda r: (r["manager_1_name"], r["manager_2_name"]))


def build_streaks(seasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    games = defaultdict(list)
    for season in seasons:
        for m in season["matchups"]:
            if not completed(m) or m["stage"] != "regular_season": continue
            for side in ("home", "away"):
                for mid in m[f"{side}_manager_ids"]:
                    games[mid].append((m["season"], m["matchup_period"], result_for(m, side)))
    output = []
    for mid, rows in games.items():
        best = {"W": 0, "L": 0}
        current_type, current = None, 0
        for _, _, outcome in sorted(rows):
            if outcome not in best: current_type, current = None, 0; continue
            if outcome == current_type: current += 1
            else: current_type, current = outcome, 1
            best[outcome] = max(best[outcome], current)
        output.append({"manager_id": mid, "manager_name": MANAGERS[mid], "longest_winning_streak": best["W"],
                       "longest_losing_streak": best["L"]})
    return sorted(output, key=lambda r: r["manager_name"])


def extreme(rows: list[dict[str, Any]], key: str, maximum: bool = True) -> dict[str, Any] | None:
    if not rows: return None
    return matchup_label((max if maximum else min)(rows, key=lambda r: r[key]))


def build_records(seasons: list[dict[str, Any]]) -> dict[str, Any]:
    matchups = [m for s in seasons for m in s["matchups"] if completed(m)]
    regular = [m for m in matchups if m["stage"] == "regular_season"]
    playoffs = [m for m in matchups if m["stage"] == "championship_playoffs"]
    playoff_series = [m for m in playoffs if m["is_multiweek_series"]]
    weekly = [w for s in seasons for w in s["weekly_scores"]]
    completed_keys = {(m["season"], m["matchup_id"]) for m in matchups}
    regular_weekly = [w for w in weekly if w["stage"] == "regular_season" and (w["season"], w["matchup_id"]) in completed_keys]
    # ESPN retains scores for teams on playoff byes. They have no opponent and
    # are not games, so exclude them from playoff-game records.
    playoff_weekly = [w for w in weekly if w["stage"] == "championship_playoffs" and w["opponent_team_id"] is not None]

    def score_extreme(rows: list[dict[str, Any]], maximum: bool) -> dict[str, Any] | None:
        return (max if maximum else min)(rows, key=lambda r: r["points"], default=None)

    champions = []
    for s in seasons:
        for team in s["teams"]:
            if s["is_complete"] and team["final_rank"] == 1:
                champions.append({"season": s["season"], "team_id": team["team_id"], "team_name": team["team_name"],
                                  "manager_ids": team["manager_ids"], "manager_names": team["manager_names"]})
    return {
        "champions": champions,
        "regular_season": {"highest_weekly_score": score_extreme(regular_weekly, True),
            "lowest_weekly_score": score_extreme(regular_weekly, False), "largest_margin": extreme(regular, "margin"),
            "closest_game": extreme(regular, "margin", False), "highest_combined_score": extreme(regular, "combined_score")},
        "championship_playoffs": {"highest_weekly_score": score_extreme(playoff_weekly, True),
            "lowest_weekly_score": score_extreme(playoff_weekly, False),
            "largest_single_week_or_round_margin": extreme([m for m in playoffs if not m["is_multiweek_series"]], "margin"),
            "closest_single_week_or_round_game": extreme([m for m in playoffs if not m["is_multiweek_series"]], "margin", False)},
        "multiweek_playoff_series": {"largest_margin": extreme(playoff_series, "margin"),
            "closest_series": extreme(playoff_series, "margin", False), "highest_combined_score": extreme(playoff_series, "combined_score")},
        "consolation_policy": "Excluded from official competitive records.",
        "counts": {"seasons": len(seasons), "team_seasons": sum(len(s["teams"]) for s in seasons),
            "regular_season_matchups": len(regular), "championship_playoff_series": len(playoffs),
            "weekly_team_scores": len(weekly), "draft_picks": sum(len(s["draft_picks"]) for s in seasons)},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=int, nargs="+", default=[2024, 2025, 2026])
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seasons = [normalize_season(args.data_root, season) for season in args.seasons]
    output = {"schema_version": 2, "league_id": seasons[0]["league_id"],
        "manager_display_policy": "First name and last initial; achievements follow managers across team-name changes.",
        "managers": [{"manager_id": mid, "manager_name": name} for mid, name in MANAGERS.items()],
        "seasons": seasons, "records": build_records(seasons), "manager_history": build_manager_history(seasons),
        "head_to_head": build_head_to_head(seasons), "streaks": build_streaks(seasons),
        "notes": ["Ed B. and Carolyn B. receive joint credit for Ed's Plus 1 Team.",
                  "Kelley H. receives sole credit for Pandamonium despite ESPN's misleading 2024 owner listing.",
                  "Airel G., Kaitlyn K., and Burke K. joined for the 2026 expansion to 14 teams.",
                  "Current-season games enter career totals and records only after ESPN marks them decided.",
                  "Consolation games are preserved but excluded from official records.",
                  "Detailed transaction history was not present in the sampled mTransactions2 response."]}
    processed = args.data_root / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    destination = processed / "core_history.json"
    serialized = json.dumps(output, indent=2)
    destination.write_text(serialized, encoding="utf-8")
    website_destination = Path("app") / "data" / "core_history.json"
    website_destination.parent.mkdir(parents=True, exist_ok=True)
    website_destination.write_text(serialized, encoding="utf-8")
    c = output["records"]["counts"]
    print(f"Wrote {destination}")
    print(f"Updated website data at {website_destination}")
    print(f"{c['seasons']} seasons, {c['team_seasons']} team-seasons, {c['regular_season_matchups']} regular-season matchups, {c['championship_playoff_series']} championship-playoff series, {c['draft_picks']} draft picks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
