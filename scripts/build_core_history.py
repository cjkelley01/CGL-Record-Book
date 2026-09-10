#!/usr/bin/env python3
"""Normalize preserved ESPN responses into the core CGL historical dataset."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required source file not found: {path}. "
            "Run scripts/discover_espn_history.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def side_score(side: dict[str, Any] | None) -> float | None:
    if not side:
        return None
    value = side.get("totalPoints")
    return float(value) if value is not None else None


def matchup_stage(period: int, regular_periods: int, tier: str | None) -> str:
    if period <= regular_periods:
        return "regular_season"
    if tier == "WINNERS_BRACKET":
        return "championship_playoffs"
    if tier == "WINNERS_CONSOLATION_LADDER":
        return "playoff_consolation"
    if tier == "LOSERS_CONSOLATION_LADDER":
        return "consolation_ladder"
    return "postseason_other"


def normalize_season(data_root: Path, season: int) -> dict[str, Any]:
    league = data_root / "raw" / str(season) / "league"
    settings_payload = read_json(league / "mSettings.json")
    teams_payload = read_json(league / "mTeam.json")
    matchup_payload = read_json(league / "mMatchupScore.json")
    draft_payload = read_json(league / "mDraftDetail.json")

    schedule_settings = settings_payload["settings"]["scheduleSettings"]
    regular_periods = int(schedule_settings["matchupPeriodCount"])
    members = {
        member["id"]: {
            "owner_id": member["id"],
            "display_name": member.get("displayName"),
        }
        for member in teams_payload.get("members", [])
    }

    teams: list[dict[str, Any]] = []
    team_lookup: dict[int, dict[str, Any]] = {}
    for team in teams_payload.get("teams", []):
        team_id = int(team["id"])
        overall = team.get("record", {}).get("overall", {})
        owner_ids = team.get("owners", [])
        normalized = {
            "season": season,
            "team_id": team_id,
            "team_season_id": f"{season}:{team_id}",
            "team_name": team.get("name") or team.get("abbrev") or f"Team {team_id}",
            "abbreviation": team.get("abbrev"),
            "owner_ids": owner_ids,
            "owner_display_names": [
                members.get(owner_id, {}).get("display_name")
                for owner_id in owner_ids
            ],
            "logo": team.get("logo"),
            "regular_season": {
                "wins": int(overall.get("wins", 0)),
                "losses": int(overall.get("losses", 0)),
                "ties": int(overall.get("ties", 0)),
                "points_for": float(overall.get("pointsFor", 0)),
                "points_against": float(overall.get("pointsAgainst", 0)),
            },
            "playoff_seed": team.get("playoffSeed"),
            "final_rank": team.get("rankCalculatedFinal"),
            "activity_totals": team.get("transactionCounter", {}),
            "source": f"data/raw/{season}/league/mTeam.json",
        }
        teams.append(normalized)
        team_lookup[team_id] = normalized

    matchups: list[dict[str, Any]] = []
    weekly_scores: list[dict[str, Any]] = []
    for matchup in matchup_payload.get("schedule", []):
        period = int(matchup["matchupPeriodId"])
        tier = matchup.get("playoffTierType")
        stage = matchup_stage(period, regular_periods, tier)
        home = matchup.get("home")
        away = matchup.get("away")
        home_id = int(home["teamId"]) if home else None
        away_id = int(away["teamId"]) if away else None
        home_score = side_score(home)
        away_score = side_score(away)
        decided = (
            home_id is not None
            and away_id is not None
            and matchup.get("winner") in {"HOME", "AWAY", "TIE"}
        )

        row = {
            "season": season,
            "matchup_id": int(matchup["id"]),
            "matchup_key": f"{season}:{matchup['id']}",
            "matchup_period": period,
            "stage": stage,
            "playoff_tier": tier,
            "playoff_round": period - regular_periods if period > regular_periods else None,
            "home_team_id": home_id,
            "home_team_name": team_lookup.get(home_id, {}).get("team_name"),
            "home_score": home_score,
            "away_team_id": away_id,
            "away_team_name": team_lookup.get(away_id, {}).get("team_name"),
            "away_score": away_score,
            "winner": matchup.get("winner"),
            "decided": decided,
            "margin": (
                abs(home_score - away_score)
                if decided and home_score is not None and away_score is not None
                else None
            ),
            "combined_score": (
                home_score + away_score
                if home_score is not None and away_score is not None
                else None
            ),
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
                    "season": season,
                    "scoring_period": int(scoring_period),
                    "matchup_period": period,
                    "stage": stage,
                    "playoff_tier": tier,
                    "matchup_id": int(matchup["id"]),
                    "team_id": team_id,
                    "team_name": team_lookup.get(team_id, {}).get("team_name"),
                    "opponent_team_id": opponent_id,
                    "opponent_team_name": team_lookup.get(opponent_id, {}).get("team_name"),
                    "points": float(points),
                    "source": f"data/raw/{season}/league/mMatchupScore.json",
                })

    picks = []
    for pick in draft_payload.get("draftDetail", {}).get("picks", []):
        team_id = int(pick["teamId"])
        picks.append({
            "season": season,
            "overall_pick": int(pick["overallPickNumber"]),
            "round": int(pick["roundId"]),
            "round_pick": int(pick["roundPickNumber"]),
            "team_id": team_id,
            "team_name": team_lookup.get(team_id, {}).get("team_name"),
            "owner_id": pick.get("memberId"),
            "player_id": int(pick["playerId"]),
            "lineup_slot_id": pick.get("lineupSlotId"),
            "keeper": bool(pick.get("keeper", False)),
            "auto_draft_type_id": pick.get("autoDraftTypeId"),
            "source": f"data/raw/{season}/league/mDraftDetail.json",
        })

    return {
        "season": season,
        "league_id": settings_payload["id"],
        "settings": {
            "team_count": len(teams),
            "regular_season_matchup_periods": regular_periods,
            "playoff_team_count": schedule_settings.get("playoffTeamCount"),
            "playoff_round_lengths": schedule_settings.get(
                "playoffMatchupPeriodLengthByRound", {}
            ),
            "playoff_reseed": schedule_settings.get("playoffReseed"),
            "playoff_seeding_rule": schedule_settings.get("playoffSeedingRule"),
        },
        "members": list(members.values()),
        "teams": sorted(teams, key=lambda row: row["team_id"]),
        "matchups": sorted(matchups, key=lambda row: row["matchup_id"]),
        "weekly_scores": sorted(
            weekly_scores,
            key=lambda row: (
                row["scoring_period"], row["team_id"], row["matchup_id"]
            ),
        ),
        "draft_picks": sorted(picks, key=lambda row: row["overall_pick"]),
    }


def completed_two_team(matchup: dict[str, Any]) -> bool:
    return bool(
        matchup["decided"]
        and matchup["home_team_id"] is not None
        and matchup["away_team_id"] is not None
        and matchup["home_score"] is not None
        and matchup["away_score"] is not None
    )


def team_result(matchup: dict[str, Any], side: str) -> str:
    winner = matchup["winner"]
    if winner == "TIE":
        return "T"
    if (side == "home" and winner == "HOME") or (
        side == "away" and winner == "AWAY"
    ):
        return "W"
    return "L"


def build_records(seasons: list[dict[str, Any]]) -> dict[str, Any]:
    all_matchups = [
        matchup
        for season in seasons
        for matchup in season["matchups"]
        if completed_two_team(matchup)
    ]
    regular = [m for m in all_matchups if m["stage"] == "regular_season"]
    championship = [
        m for m in all_matchups if m["stage"] == "championship_playoffs"
    ]
    all_weekly = [
        score for season in seasons for score in season["weekly_scores"]
    ]
    regular_weekly = [
        score for score in all_weekly if score["stage"] == "regular_season"
    ]

    def matchup_label(m: dict[str, Any]) -> dict[str, Any]:
        return {
            "season": m["season"],
            "matchup_period": m["matchup_period"],
            "stage": m["stage"],
            "home_team": m["home_team_name"],
            "home_score": m["home_score"],
            "away_team": m["away_team_name"],
            "away_score": m["away_score"],
            "margin": m["margin"],
            "combined_score": m["combined_score"],
        }

    team_games: list[dict[str, Any]] = []
    for matchup in all_matchups:
        for side, opponent in (("home", "away"), ("away", "home")):
            team_games.append({
                "season": matchup["season"],
                "matchup_period": matchup["matchup_period"],
                "stage": matchup["stage"],
                "team_id": matchup[f"{side}_team_id"],
                "team_name": matchup[f"{side}_team_name"],
                "opponent_team_id": matchup[f"{opponent}_team_id"],
                "opponent_team_name": matchup[f"{opponent}_team_name"],
                "points": matchup[f"{side}_score"],
                "opponent_points": matchup[f"{opponent}_score"],
                "result": team_result(matchup, side),
            })

    wins = [game for game in team_games if game["result"] == "W"]
    losses = [game for game in team_games if game["result"] == "L"]

    return {
        "champions": [
            {
                "season": season["season"],
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "owner_ids": team["owner_ids"],
            }
            for season in seasons
            for team in season["teams"]
            if team["final_rank"] == 1
        ],
        "highest_regular_season_week": max(
            regular_weekly, key=lambda row: row["points"], default=None
        ),
        "lowest_regular_season_week": min(
            regular_weekly, key=lambda row: row["points"], default=None
        ),
        "largest_margin": (
            matchup_label(max(all_matchups, key=lambda row: row["margin"]))
            if all_matchups else None
        ),
        "closest_game": (
            matchup_label(min(all_matchups, key=lambda row: row["margin"]))
            if all_matchups else None
        ),
        "highest_combined_score": (
            matchup_label(max(all_matchups, key=lambda row: row["combined_score"]))
            if all_matchups else None
        ),
        "highest_score_in_loss": max(
            losses, key=lambda row: row["points"], default=None
        ),
        "lowest_score_in_win": min(
            wins, key=lambda row: row["points"], default=None
        ),
        "counts": {
            "seasons": len(seasons),
            "teams": sum(len(season["teams"]) for season in seasons),
            "regular_season_matchups": len(regular),
            "championship_playoff_matchups": len(championship),
            "weekly_team_scores": len(all_weekly),
            "draft_picks": sum(len(season["draft_picks"]) for season in seasons),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=int, nargs="+", default=[2024, 2025])
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seasons = [normalize_season(args.data_root, season) for season in args.seasons]
    output = {
        "schema_version": 1,
        "league_id": seasons[0]["league_id"],
        "seasons": seasons,
        "records": build_records(seasons),
        "notes": [
            "Manager aliases are not inferred from team names.",
            "Transaction detail was not present in the sampled mTransactions2 view.",
            "Weekly lineup history will be normalized in a later milestone.",
        ],
    }
    processed = args.data_root / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    destination = processed / "core_history.json"
    destination.write_text(json.dumps(output, indent=2), encoding="utf-8")
    counts = output["records"]["counts"]
    print(f"Wrote {destination}")
    print(
        f"{counts['seasons']} seasons, {counts['teams']} team-seasons, "
        f"{counts['regular_season_matchups']} regular-season matchups, "
        f"{counts['championship_playoff_matchups']} championship-playoff matchups, "
        f"{counts['draft_picks']} draft picks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
