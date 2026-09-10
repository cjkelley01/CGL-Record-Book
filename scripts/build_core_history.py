#!/usr/bin/env python3
"""Normalize preserved ESPN responses into the CGL historical record book."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests


MANAGERS = {
    "charley_k": "Charley K.", "quy_h": "Quy H.", "mike_k": "Mike K.",
    "robin_h": "Robin H.", "jj_k": "JJ K.", "alex_h": "Alex H.",
    "tony_r": "Tony R.", "kelley_h": "Kelley H.", "susan_h": "Susan H.",
    "charley_b": "Charley B.", "ed_carolyn_b": "Ed B. & Carolyn B.",
    "timmy_k": "Timmy K.", "aaron_t": "Aaron T.", "emma_t": "Emma T.",
    "joseph_e": "Joseph E.", "airel_g": "Airel G.",
    "kaitlyn_k": "Kaitlyn K.", "burke_k": "Burke K.",
}

CURRENT_TEAM_NAME_MANAGERS = {
    "charley s angels": ["charley_k"], "kinda mid": ["aaron_t"],
    "mike s magic": ["mike_k"], "all the way to the em zone": ["emma_t"],
    "no refills": ["jj_k"], "flux capacitors": ["tony_r"],
    "big joe": ["joseph_e"], "sos": ["susan_h"],
    "cb s bulls": ["charley_b"], "ed s plus 1 team": ["ed_carolyn_b"],
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
    (2024, 17): ["ed_carolyn_b"], (2024, 18): ["timmy_k"],
    (2025, 1): ["charley_k"], (2025, 2): ["aaron_t"],
    (2025, 3): ["mike_k"], (2025, 4): ["emma_t"],
    (2025, 5): ["jj_k"], (2025, 8): ["alex_h"],
    (2025, 9): ["tony_r"], (2025, 10): ["joseph_e"],
    (2025, 13): ["susan_h"], (2025, 14): ["charley_b"],
    (2025, 17): ["ed_carolyn_b"], (2025, 18): ["timmy_k"],
}

# ESPN's defaultPositionId values are player positions, not lineup-slot IDs.
POSITION_NAMES = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}

DEFENSE_NAMES = {
    -16001: "Atlanta Falcons D/ST", -16002: "Buffalo Bills D/ST", -16003: "Chicago Bears D/ST",
    -16004: "Cincinnati Bengals D/ST", -16005: "Cleveland Browns D/ST", -16006: "Dallas Cowboys D/ST",
    -16007: "Denver Broncos D/ST", -16008: "Detroit Lions D/ST", -16009: "Green Bay Packers D/ST",
    -16010: "Tennessee Titans D/ST", -16011: "Indianapolis Colts D/ST", -16012: "Kansas City Chiefs D/ST",
    -16013: "Las Vegas Raiders D/ST", -16014: "Los Angeles Rams D/ST", -16015: "Miami Dolphins D/ST",
    -16016: "Minnesota Vikings D/ST", -16017: "New England Patriots D/ST", -16018: "New Orleans Saints D/ST",
    -16019: "New York Giants D/ST", -16020: "New York Jets D/ST", -16021: "Philadelphia Eagles D/ST",
    -16022: "Arizona Cardinals D/ST", -16023: "Pittsburgh Steelers D/ST", -16024: "Los Angeles Chargers D/ST",
    -16025: "San Francisco 49ers D/ST", -16026: "Seattle Seahawks D/ST", -16027: "Tampa Bay Buccaneers D/ST",
    -16028: "Washington Commanders D/ST", -16029: "Carolina Panthers D/ST", -16030: "Jacksonville Jaguars D/ST",
    -16033: "Baltimore Ravens D/ST", -16034: "Houston Texans D/ST",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}. Run scripts/discover_espn_history.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def player_catalog(data_root: Path, season: int) -> dict[int, dict[str, Any]]:
    """Collect ESPN player metadata from every preserved roster and box-score response."""
    catalog: dict[int, dict[str, Any]] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            player_id, full_name = value.get("id"), value.get("fullName")
            if isinstance(player_id, int) and isinstance(full_name, str) and full_name.strip():
                catalog[player_id] = {
                    "player_name": full_name.strip(),
                    "default_position_id": value.get("defaultPositionId"),
                    "pro_team_id": value.get("proTeamId"),
                }
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    season_root = data_root / "raw" / str(season)
    candidates = list((season_root / "league").glob("mRoster.json"))
    candidates.extend((season_root / "weeks").glob("**/mRoster.json"))
    candidates.extend((season_root / "weeks").glob("**/mBoxscore.json"))
    for path in candidates:
        visit(read_json(path))
    return catalog


def resolve_draft_players(data_root: Path, season: int, catalog: dict[int, dict[str, Any]], player_ids: set[int]) -> None:
    """Fill gaps left by archived rosters using defense IDs and ESPN's public athlete record."""
    cache_path = data_root / "processed" / "espn_player_catalog.json"
    cache: dict[str, dict[str, Any]] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    for player_id in player_ids:
        if player_id in catalog:
            continue
        if player_id in DEFENSE_NAMES:
            catalog[player_id] = {"player_name": DEFENSE_NAMES[player_id], "position": "D/ST", "pro_team_id": None}
        elif str(player_id) in cache:
            catalog[player_id] = cache[str(player_id)]

    session = requests.Session()
    session.headers.update({"User-Agent": "CGL-Record-Book/1.0"})
    for player_id in sorted(player_ids):
        if player_id <= 0 or player_id in catalog:
            continue
        endpoints = [
            f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{player_id}",
            f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/athletes/{player_id}",
        ]
        for url in endpoints:
            try:
                response = session.get(url, timeout=10)
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError):
                continue
            athlete = payload.get("athlete", payload)
            player_name = athlete.get("displayName") or athlete.get("fullName")
            position_data = athlete.get("position") or {}
            position = position_data.get("abbreviation") if isinstance(position_data, dict) else None
            if player_name:
                catalog[player_id] = {
                    "player_name": player_name,
                    "position": position,
                    "default_position_id": athlete.get("defaultPositionId"),
                    "pro_team_id": athlete.get("proTeamId"),
                }
                cache[str(player_id)] = catalog[player_id]
                break

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    players = player_catalog(data_root, season)
    draft_player_ids = {int(pick["playerId"]) for pick in draft_payload.get("draftDetail", {}).get("picks", [])}
    resolve_draft_players(data_root, season, players, draft_player_ids)
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
        player_id = int(pick["playerId"])
        player = players.get(player_id, {})
        picks.append({
            "season": season, "overall_pick": int(pick["overallPickNumber"]), "round": int(pick["roundId"]),
            "round_pick": int(pick["roundPickNumber"]), "team_id": team_id,
            "team_name": team_lookup[team_id]["team_name"], "manager_ids": team_lookup[team_id]["manager_ids"],
            "manager_names": team_lookup[team_id]["manager_names"], "player_id": player_id,
            "player_name": player.get("player_name"),
            "position": POSITION_NAMES.get(player.get("default_position_id")) or player.get("position"),
            "pro_team_id": player.get("pro_team_id"), "player_resolved": bool(player.get("player_name")),
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


def add_season_archives(seasons: list[dict[str, Any]]) -> None:
    """Attach annual awards and concise, data-supported season narratives."""
    previous_teams: dict[str, str] = {}
    previous_team_count: int | None = None
    for season in seasons:
        regular_games = [m for m in season["matchups"] if m["stage"] == "regular_season" and completed(m)]
        completed_ids = {m["matchup_id"] for m in regular_games}
        regular_scores = [s for s in season["weekly_scores"] if s["stage"] == "regular_season" and s["matchup_id"] in completed_ids]
        team_results = []
        for matchup in regular_games:
            for side, opponent in (("home", "away"), ("away", "home")):
                team_results.append({
                    "team_name": matchup[f"{side}_team_name"], "manager_names": matchup[f"{side}_manager_names"],
                    "points": matchup[f"{side}_score"], "opponent_team_name": matchup[f"{opponent}_team_name"],
                    "opponent_points": matchup[f"{opponent}_score"], "week": matchup["scoring_periods"][0],
                    "result": result_for(matchup, side),
                })

        seeded = sorted(season["teams"], key=lambda t: (t["playoff_seed"] or 999))
        points_leader = max(season["teams"], key=lambda t: t["regular_season"]["points_for"], default=None)
        champion = next((t for t in season["teams"] if season["is_complete"] and t["final_rank"] == 1), None)
        runner_up = next((t for t in season["teams"] if season["is_complete"] and t["final_rank"] == 2), None)
        championship = next((m for m in season["matchups"] if m["stage"] == "championship_playoffs" and m["is_multiweek_series"] and completed(m)), None)
        highest = max(regular_scores, key=lambda s: s["points"], default=None)
        lowest = min(regular_scores, key=lambda s: s["points"], default=None)
        largest = max(regular_games, key=lambda m: m["margin"], default=None)
        closest = min(regular_games, key=lambda m: m["margin"], default=None)
        high_loss = max((r for r in team_results if r["result"] == "L"), key=lambda r: r["points"], default=None)
        low_win = min((r for r in team_results if r["result"] == "W"), key=lambda r: r["points"], default=None)

        awards = []
        def award(key: str, title: str, row: dict[str, Any] | None, value: str, detail: str) -> None:
            if row:
                awards.append({"key": key, "title": title, "team_name": row.get("team_name"),
                               "manager_names": row.get("manager_names", []), "value": value, "detail": detail})

        award("champion", "Champion", champion, "CGL Champion", f"#{champion['playoff_seed']} seed" if champion else "")
        award("runner_up", "Runner-up", runner_up, "League finalist", f"#{runner_up['playoff_seed']} seed" if runner_up else "")
        if seeded:
            award("regular_winner", "Regular-season winner", seeded[0], f"{seeded[0]['regular_season']['wins']}–{seeded[0]['regular_season']['losses']}", "#1 seed")
        if points_leader:
            award("points_leader", "Points leader", points_leader, f"{points_leader['regular_season']['points_for']:.2f}", "regular-season points")
        award("highest_score", "Highest weekly score", highest, f"{highest['points']:.2f}" if highest else "", f"Week {highest['scoring_period']}" if highest else "")
        award("lowest_score", "Lowest weekly score", lowest, f"{lowest['points']:.2f}" if lowest else "", f"Week {lowest['scoring_period']}" if lowest else "")
        if largest:
            winner_side = "home" if largest["winner"] == "HOME" else "away"
            award("biggest_blowout", "Biggest blowout", {"team_name": largest[f"{winner_side}_team_name"], "manager_names": largest[f"{winner_side}_manager_names"]}, f"{largest['margin']:.2f}", f"over {largest['away_team_name'] if winner_side == 'home' else largest['home_team_name']} · Week {largest['matchup_period']}")
        if closest:
            winner_side = "home" if closest["winner"] == "HOME" else "away"
            award("closest_game", "Closest game", {"team_name": closest[f"{winner_side}_team_name"], "manager_names": closest[f"{winner_side}_manager_names"]}, f"{closest['margin']:.2f}", f"over {closest['away_team_name'] if winner_side == 'home' else closest['home_team_name']} · Week {closest['matchup_period']}")
        award("highest_loss", "Highest score in a loss", high_loss, f"{high_loss['points']:.2f}" if high_loss else "", f"vs. {high_loss['opponent_team_name']} · Week {high_loss['week']}" if high_loss else "")
        award("lowest_win", "Lowest score in a win", low_win, f"{low_win['points']:.2f}" if low_win else "", f"vs. {low_win['opponent_team_name']} · Week {low_win['week']}" if low_win else "")
        season["awards"] = awards

        stories = []
        if champion and runner_up and championship:
            champion_score = championship["home_score"] if championship["home_team_id"] == champion["team_id"] else championship["away_score"]
            runner_score = championship["away_score"] if championship["home_team_id"] == champion["team_id"] else championship["home_score"]
            stories.append({"label": "Championship path", "title": f"{champion['team_name']} finishes the climb",
                            "text": f"The #{champion['playoff_seed']} seed went {champion['regular_season']['wins']}–{champion['regular_season']['losses']} before defeating {runner_up['team_name']} {champion_score:.2f}–{runner_score:.2f} in the two-week final."})
            if champion["playoff_seed"] >= 4:
                stories.append({"label": "Cinderella champion", "title": f"A #{champion['playoff_seed']} seed takes the title",
                                "text": f"{champion['team_name']} won the championship from outside the regular season's top three."})
        if seeded and points_leader:
            if seeded[0]["team_id"] == points_leader["team_id"]:
                stories.append({"label": "Regular-season force", "title": f"{seeded[0]['team_name']} sets the pace",
                                "text": f"The #1 seed also led the league with {points_leader['regular_season']['points_for']:.2f} regular-season points."})
            else:
                stories.append({"label": "Split supremacy", "title": "Two teams owned the regular season",
                                "text": f"{seeded[0]['team_name']} earned the #1 seed, while {points_leader['team_name']} led scoring with {points_leader['regular_season']['points_for']:.2f} points."})
        if high_loss:
            stories.append({"label": "Heartbreaker", "title": f"{high_loss['team_name']} scores {high_loss['points']:.2f} and still loses",
                            "text": f"{high_loss['opponent_team_name']} survived the season's highest losing score in Week {high_loss['week']}."})
        if closest:
            stories.append({"label": "Photo finish", "title": f"Decided by {closest['margin']:.2f} points",
                            "text": f"{closest['home_team_name']} and {closest['away_team_name']} produced the season's closest game in Week {closest['matchup_period']}."})
        if largest:
            stories.append({"label": "Statement win", "title": f"A {largest['margin']:.2f}-point rout",
                            "text": f"{largest['home_team_name']} and {largest['away_team_name']} played the season's largest blowout in Week {largest['matchup_period']}."})
        current_count = len(season["teams"])
        if previous_team_count is not None and current_count > previous_team_count:
            newcomers = [t["team_name"] for t in season["teams"] if all(mid not in previous_teams for mid in t["manager_ids"])]
            stories.insert(0, {"label": "Expansion", "title": f"CGL grows to {current_count} teams",
                               "text": f"{', '.join(newcomers)} joined the league for {season['season']}."})
        changed = []
        for team in season["teams"]:
            for manager_id in team["manager_ids"]:
                old_name = previous_teams.get(manager_id)
                if old_name and old_name != team["team_name"]:
                    changed.append(f"{old_name} became {team['team_name']}")
                previous_teams[manager_id] = team["team_name"]
        if changed:
            stories.append({"label": "New identities", "title": "Team names changed", "text": "; ".join(changed) + "."})
        season["storylines"] = stories
        previous_team_count = current_count


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

    regular_team_results = []
    for matchup in regular:
        for side, opponent in (("home", "away"), ("away", "home")):
            regular_team_results.append({
                "season": matchup["season"],
                "scoring_period": matchup["scoring_periods"][0],
                "matchup_period": matchup["matchup_period"],
                "team_id": matchup[f"{side}_team_id"],
                "team_name": matchup[f"{side}_team_name"],
                "manager_ids": matchup[f"{side}_manager_ids"],
                "manager_names": matchup[f"{side}_manager_names"],
                "opponent_team_id": matchup[f"{opponent}_team_id"],
                "opponent_team_name": matchup[f"{opponent}_team_name"],
                "points": matchup[f"{side}_score"],
                "opponent_points": matchup[f"{opponent}_score"],
                "result": result_for(matchup, side),
            })

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
            "closest_game": extreme(regular, "margin", False), "highest_combined_score": extreme(regular, "combined_score"),
            "highest_score_in_loss": max((row for row in regular_team_results if row["result"] == "L"), key=lambda row: row["points"], default=None),
            "lowest_score_in_win": min((row for row in regular_team_results if row["result"] == "W"), key=lambda row: row["points"], default=None)},
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
    add_season_archives(seasons)
    output = {"schema_version": 2, "league_id": seasons[0]["league_id"],
        "manager_display_policy": "First name and last initial; achievements follow managers across team-name changes.",
        "managers": [{"manager_id": mid, "manager_name": name} for mid, name in MANAGERS.items()],
        "seasons": seasons, "records": build_records(seasons), "manager_history": build_manager_history(seasons),
        "head_to_head": build_head_to_head(seasons), "streaks": build_streaks(seasons),
        "notes": ["Ed B. & Carolyn B. are one permanent joint ownership unit for Ed's Plus 1 Team.",
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
    draft_picks = [pick for season in seasons for pick in season["draft_picks"]]
    unresolved_ids = sorted({pick["player_id"] for pick in draft_picks if not pick["player_resolved"]})
    print(f"Resolved player names for {len(draft_picks) - sum(not pick['player_resolved'] for pick in draft_picks)}/{len(draft_picks)} draft selections.")
    if unresolved_ids:
        print("Unresolved ESPN player IDs: " + ", ".join(map(str, unresolved_ids)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
