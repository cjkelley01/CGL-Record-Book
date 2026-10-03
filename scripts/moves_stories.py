"""Curated, validated editorial stories built from normalized move evidence."""

from __future__ import annotations

from typing import Any


STORY_MANIFEST: list[dict[str, Any]] = [
    {
        "id": "six-player-jolt-2025",
        "story_type": "lead",
        "priority": 100,
        "transaction_ids": ["8ab7a921-b91e-453d-a321-058f49dcdf0c"],
        "manager_ids": ["charley_k", "emma_t"],
        "expected_players": ["Patrick Mahomes", "Ashton Jeanty", "Terry McLaurin", "T.J. Hockenson", "Brian Thomas Jr.", "Baker Mayfield"],
        "headline": "A six-player jolt—and a season that still slipped away",
        "label": "2025 · Blockbuster trade",
        "context": "Charley’s Angels entered Week {week} at {charley_before}, while All the way to the Em-zone stood {emma_before}. The deal landed at a clear pivot point for both teams.",
        "decision": "Charley K. acquired Patrick Mahomes, Ashton Jeanty and Terry McLaurin. Emma T. received T.J. Hockenson, Brian Thomas Jr. and Baker Mayfield in the same six-player deal.",
        "aftermath": "Mahomes and Jeanty supplied {charley_points} starting-lineup points for Charley; McLaurin never entered a CGL starting lineup during that stint. Charley won the next {charley_streak} games, but finished {charley_final} and missed the playoffs. Emma’s return supplied {emma_points} starter points, and her team finished {emma_final}.",
        "evidence": ["{charley_points} starter points received by Charley", "{emma_points} starter points received by Emma", "Final records: {charley_final} and {emma_final}"],
    },
    {
        "id": "four-star-trade-2024",
        "story_type": "feature",
        "priority": 90,
        "transaction_ids": ["5fb7fe22-d944-4ada-a2cf-3e0bc4f5bce2"],
        "manager_ids": ["charley_k", "charley_b"],
        "expected_players": ["D'Andre Swift", "A.J. Brown", "Tyreek Hill", "Chuba Hubbard"],
        "headline": "A twelfth-round pick became part of a championship deal",
        "draft_picks": [{"season": 2024, "manager_id": "charley_k", "player_name": "Chuba Hubbard", "round": 12, "overall_pick": 142}],
        "label": "2024 · Foundational trade",
        "context": "Charley’s Angels and CB’s Bulls were both {shared_before} when they completed one of the archive’s largest deals before Week {week}.",
        "decision": "Charley K. had drafted Chuba Hubbard in Round {hubbard_round}, {hubbard_pick}nd overall. Before Week {week}, he packaged that late-round pick with Tyreek Hill for D’Andre Swift and A.J. Brown. CB’s Bulls put both Hill and Hubbard to work; all four players became starters for their new teams.",
        "aftermath": "Swift and Brown produced {charley_points} starter points, including {charley_playoff_points} in the championship bracket. Hill and Hubbard produced {cb_points} for CB’s Bulls. Charley’s Angels finished {charley_final} and won the title; CB’s Bulls finished {cb_final}.",
        "evidence": ["{combined_points} combined starter points", "{charley_playoff_points} playoff points from Swift and Brown", "Charley’s Angels: 2024 champion"],
    },
    {
        "id": "timberwolves-waiver-rhythm",
        "story_type": "cross_year",
        "priority": 80,
        "transaction_ids": [
            "25f45eab-b531-44a8-87b5-546bea6340f2",
            "7b8164c4-32b9-4aba-bfc7-a02edd9bf066",
            "a460057c-2aa5-416e-82a4-4a847e0ea081",
            "2cf2c1c4-8944-420d-bcc3-36a6c7ce1044",
        ],
        "manager_ids": ["timmy_k"],
        "expected_players": ["Chase Brown", "Quinshon Judkins", "George Kittle"],
        "headline": "The first pick went missing. An eleventh-rounder got a second chance.",
        "draft_picks": [
            {"season": 2024, "manager_id": "timmy_k", "player_name": "Christian McCaffrey", "round": 1, "overall_pick": 1},
            {"season": 2024, "manager_id": "timmy_k", "player_name": "Chase Brown", "round": 11, "overall_pick": 121},
        ],
        "label": "{span} · Sustained success",
        "context": "Timmy K. opened the 2024 draft with Christian McCaffrey at No. {cmc_pick}. McCaffrey’s Achilles trouble kept him out through Week 9, leaving the Timberwolves without their first overall pick for most of the regular season. One answer was a player Timmy had already drafted—and let go.",
        "decision": "Chase Brown arrived in Round {brown_round}, pick {brown_pick}. Timmy dropped him for Cam Akers in Week {drop_week}, then reversed the move {return_days} days later. Back with the Timberwolves, Brown became a regular starter and supplied {brown_points} points, including {brown_playoff_points} in the playoffs.",
        "aftermath": "The Timberwolves finished {record_2024} in 2024. Timmy found more help after draft day the following year: Quinshon Judkins and George Kittle supplied {year_2025_points} starting-lineup points between them, and the team finished {record_2025}. Across the two seasons, those three additions supplied {total_points} points in {total_starts} starts.",
        "evidence": ["3 distinct acquisitions", "{total_points} starter points", "{total_starts} starts across {span}"],
    },
    {
        "id": "flux-defense-carousel-2025",
        "story_type": "feature",
        "priority": 70,
        "transaction_ids": [
            "3edb841d-03d2-479b-941d-f82da62c5acd",
            "76a8b39b-22f5-4b1c-b1a2-ec721a56889d",
            "a43fba00-bccc-4726-99cf-e44890f46f32",
            "a4098203-b56d-4ae9-af50-7a5ee7102a32",
        ],
        "manager_ids": ["tony_r"],
        "expected_players": ["Jaguars D/ST", "Saints D/ST", "Steelers D/ST", "Raiders D/ST"],
        "headline": "Four defenses, four playoff weeks, one championship",
        "label": "2025 · Championship reinforcements",
        "context": "Flux Capacitors entered the 2025 championship bracket as the #{seed} seed after a {record} regular season.",
        "decision": "Tony R. used four separate acquisitions for four consecutive playoff weeks: Jacksonville, New Orleans, Pittsburgh and Las Vegas.",
        "aftermath": "Each defense made one championship-bracket start and the group scored {playoff_points} points. Flux Capacitors finished the run as CGL champion.",
        "evidence": ["4 separate acquisitions", "{playoff_points} playoff points", "2025 CGL champion"],
    },
    {
        "id": "tee-higgins-got-away-2024",
        "story_type": "timeline",
        "priority": 60,
        "transaction_ids": [
            "3810c1f2-881c-415c-8158-26fde22da5f9",
            "62627426-115c-430b-b16e-790d8bf8d0a7",
        ],
        "manager_ids": ["charley_b", "timmy_k"],
        "expected_players": ["Tee Higgins", "Alexander Mattison"],
        "headline": "Tee Higgins crossed the waiver wire—and resurfaced in the playoffs",
        "label": "2024 · The one that got away",
        "context": "CB’s Bulls released Tee Higgins while adding Alexander Mattison in Week 2.",
        "decision": "The Timberwolves added Higgins the following week and later used him for seven starts.",
        "aftermath": "Higgins delivered {total_points} starter points for Timmy K., including {playoff_points} across two championship-bracket starts. Mattison produced {mattison_points} points in two starts for CB’s Bulls. A September release had become a December contributor for another contender.",
        "evidence": ["{total_points} points after the pickup", "{playoff_points} playoff points", "7 starts for the Timberwolves"],
    },
    {
        "id": "bucky-irving-breakout-2024",
        "story_type": "brief",
        "priority": 50,
        "transaction_ids": ["2aa9e835-88b4-4617-9749-c77c286c266d"],
        "manager_ids": ["mike_k"],
        "expected_players": ["Bucky Irving"],
        "headline": "Bucky Irving broke out, even if Mike’s season did not",
        "label": "2024 · Waiver find",
        "context": "Mike’s Magic was {before} when Bucky Irving arrived before Week {week}.",
        "decision": "Mike K. added Irving as a free agent and eventually started him eleven times.",
        "aftermath": "Irving supplied {points} regular-season points, the strongest pickup contribution in the 2024 archive. Mike’s Magic recovered from its winless start to finish {final}. Irving became a bright spot even as the team missed the playoffs.",
        "evidence": ["{points} starter points", "11 starts", "Final record: {final}"],
    },

]


def _record(team_id: int, season: dict[str, Any], *, before_week: int | None = None) -> tuple[int, int, int]:
    wins = losses = ties = 0
    for matchup in season["matchups"]:
        if matchup["stage"] != "regular_season" or team_id not in (matchup["home_team_id"], matchup["away_team_id"]):
            continue
        week = min(matchup["scoring_periods"])
        if before_week is not None and week >= before_week:
            continue
        side = "home" if matchup["home_team_id"] == team_id else "away"
        if matchup["winner"] == "TIE": ties += 1
        elif matchup["winner"] == side.upper(): wins += 1
        else: losses += 1
    return wins, losses, ties


def _record_text(record: tuple[int, int, int]) -> str:
    wins, losses, ties = record
    return f"{wins}–{losses}" + (f"–{ties}" if ties else "")


def _winning_streak_from(team_id: int, season: dict[str, Any], week: int) -> int:
    results = []
    for matchup in sorted(season["matchups"], key=lambda row: min(row["scoring_periods"])):
        if matchup["stage"] != "regular_season" or min(matchup["scoring_periods"]) < week:
            continue
        if team_id not in (matchup["home_team_id"], matchup["away_team_id"]):
            continue
        side = "home" if matchup["home_team_id"] == team_id else "away"
        results.append(matchup["winner"] == side.upper())
    return next((index for index, won in enumerate(results) if not won), len(results))


def _side(move: dict[str, Any], manager_id: str) -> dict[str, Any]:
    return next(side for side in move["sides"] if manager_id in side["manager_ids"])


def _player(move: dict[str, Any], player_name: str) -> dict[str, Any]:
    return next(player for side in move["sides"] for player in side["acquired"] if player["player_name"] == player_name)


def _team(season: dict[str, Any], manager_id: str) -> dict[str, Any]:
    return next(team for team in season["teams"] if manager_id in team["manager_ids"])


def _draft(seasons: dict[int, dict[str, Any]], year: int, manager: str, player: str) -> dict[str, Any]:
    matches = [pick for pick in seasons[year]["draft_picks"]
               if manager in pick["manager_ids"] and pick["player_name"] == player]
    if len(matches) != 1:
        raise ValueError(f"Expected one draft pick for {year} {manager} {player}")
    return matches[0]


def _validate_drafts(definition: dict[str, Any], seasons: dict[int, dict[str, Any]]) -> None:
    for reference in definition.get("draft_picks", []):
        pick = _draft(seasons, reference["season"], reference["manager_id"], reference["player_name"])
        if any(pick[key] != reference[key] for key in ("round", "overall_pick")):
            raise ValueError(f"Story {definition['id']} draft evidence changed: {reference['player_name']}")


def _facts(definition: dict[str, Any], events: list[dict[str, Any]], seasons: dict[int, dict[str, Any]]) -> dict[str, str]:
    first = events[0]
    season = seasons[first["season"]]
    if definition["id"] == "six-player-jolt-2025":
        charley, emma = _side(first, "charley_k"), _side(first, "emma_t")
        return {"week": str(first["week"]), "charley_before": _record_text(_record(charley["team_id"], season, before_week=first["week"])),
                "emma_before": _record_text(_record(emma["team_id"], season, before_week=first["week"])),
                "charley_points": f'{charley["contribution"]["total_points"]:.2f}', "emma_points": f'{emma["contribution"]["total_points"]:.1f}',
                "charley_streak": str(_winning_streak_from(charley["team_id"], season, first["week"])),
                "charley_final": _record_text(_record(charley["team_id"], season)), "emma_final": _record_text(_record(emma["team_id"], season))}
    if definition["id"] == "four-star-trade-2024":
        charley, cb = _side(first, "charley_k"), _side(first, "charley_b")
        cp, bp = charley["contribution"], cb["contribution"]
        before = _record_text(_record(charley["team_id"], season, before_week=first["week"]))
        if before != _record_text(_record(cb["team_id"], season, before_week=first["week"])):
            raise ValueError(f"Story {definition['id']} expected a shared pre-trade record")
        hubbard = _draft(seasons, 2024, "charley_k", "Chuba Hubbard")
        return {"hubbard_round": str(hubbard["round"]), "hubbard_pick": str(hubbard["overall_pick"]), "week": str(first["week"]), "shared_before": before, "charley_points": f'{cp["total_points"]:.1f}',
                "charley_playoff_points": f'{cp["playoff_points"]:.1f}', "cb_points": f'{bp["total_points"]:.1f}',
                "combined_points": f'{cp["total_points"] + bp["total_points"]:.1f}',
                "charley_final": _record_text(_record(charley["team_id"], season)), "cb_final": _record_text(_record(cb["team_id"], season))}
    if definition["id"] == "timberwolves-waiver-rhythm":
        # The Akers transaction supplies departure evidence, not a fourth success.
        successes = [event for event in events if event["id"] != "7b8164c4-32b9-4aba-bfc7-a02edd9bf066"]
        contributions = [_side(event, "timmy_k")["contribution"] for event in successes]
        from datetime import date
        departure = events[1]
        if not any(p["player_name"] == "Chase Brown" for p in _side(departure, "timmy_k")["outgoing"]):
            raise ValueError("Brown departure evidence changed")
        brown = _draft(seasons, 2024, "timmy_k", "Chase Brown")
        cmc = _draft(seasons, 2024, "timmy_k", "Christian McCaffrey")
        years = sorted({event["season"] for event in events})
        return {"cmc_pick": str(cmc["overall_pick"]), "brown_round": str(brown["round"]), "brown_pick": str(brown["overall_pick"]),
                "drop_week": str(departure["week"]), "return_days": str((date.fromisoformat(first["date"]) - date.fromisoformat(departure["date"])).days),
                "brown_points": f'{_player(first, "Chase Brown")["contribution"]["total_points"]:.1f}',
                "record_2024": _record_text(_record(_team(seasons[2024], "timmy_k")["team_id"], seasons[2024])),
                "record_2025": _record_text(_record(_team(seasons[2025], "timmy_k")["team_id"], seasons[2025])),
                "span": f"{years[0]}–{years[-1]}", "total_points": f'{sum(row["total_points"] for row in contributions):.1f}',
                "total_starts": str(sum(row["total_starts"] for row in contributions)),
                "brown_playoff_points": f'{_player(events[0], "Chase Brown")["contribution"]["playoff_points"]:.1f}',
                "year_2025_points": f'{sum(_side(event, "timmy_k")["contribution"]["total_points"] for event in events if event["season"] == 2025):.1f}'}
    if definition["id"] == "flux-defense-carousel-2025":
        team = _team(season, "tony_r")
        return {"seed": str(team["playoff_seed"]), "record": _record_text(_record(team["team_id"], season)),
                "playoff_points": f'{sum(_side(event, "tony_r")["contribution"]["playoff_points"] for event in events):.1f}'}
    if definition["id"] == "tee-higgins-got-away-2024":
        acquisition = events[1]
        higgins = _player(acquisition, "Tee Higgins")["contribution"]
        mattison = _player(events[0], "Alexander Mattison")["contribution"]
        return {"total_points": f'{higgins["total_points"]:.1f}', "playoff_points": f'{higgins["playoff_points"]:.1f}',
                "mattison_points": f'{mattison["total_points"]:.1f}'}
    if definition["id"] == "bucky-irving-breakout-2024":
        side = _side(first, "mike_k")
        return {"before": _record_text(_record(side["team_id"], season, before_week=first["week"])),
                "week": str(first["week"]), "points": f'{side["contribution"]["regular_points"]:.1f}',
                "final": _record_text(_record(side["team_id"], season))}
    raise ValueError(f"No fact builder for story {definition['id']}")


def validate_unique_event_coverage(definitions: list[dict[str, Any]]) -> None:
    claimed: dict[str, str] = {}
    for definition in definitions:
        for event_id in definition["transaction_ids"]:
            if event_id in claimed:
                raise ValueError(f"Transaction {event_id} is retold by {claimed[event_id]} and {definition['id']}")
            claimed[event_id] = definition["id"]


def filter_stories(stories: list[dict[str, Any]], season: int | None) -> list[dict[str, Any]]:
    """A cross-year story remains whole when any supporting event is in the selected year."""
    return [story for story in stories if season is None or season in story["relevant_seasons"]]


def build_stories(moves: list[dict[str, Any]], seasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve the editorial manifest and fail loudly when its evidence goes stale."""
    move_by_id = {move["id"]: move for move in moves}
    season_by_year = {season["season"]: season for season in seasons}
    validate_unique_event_coverage(STORY_MANIFEST)
    stories = []
    for definition in STORY_MANIFEST:
        missing = [event_id for event_id in definition["transaction_ids"] if event_id not in move_by_id]
        if missing:
            raise ValueError(f"Story {definition['id']} is missing supporting transactions: {', '.join(missing)}")
        events = [move_by_id[event_id] for event_id in definition["transaction_ids"]]
        actual_managers = {manager_id for event in events for side in event["sides"] for manager_id in side["manager_ids"]}
        if not set(definition["manager_ids"]).issubset(actual_managers):
            raise ValueError(f"Story {definition['id']} manager identities no longer match its evidence")
        actual_players = {player["player_name"] for event in events for side in event["sides"] for player in side["acquired"]}
        actual_players.update(outgoing["player_name"] for event in events for side in event["sides"] for outgoing in side["outgoing"])
        if not set(definition["expected_players"]).issubset(actual_players):
            raise ValueError(f"Story {definition['id']} player identities no longer match its evidence")
        relevant_seasons = sorted({event["season"] for event in events})
        _validate_drafts(definition, season_by_year)
        facts = _facts(definition, events, season_by_year)
        stories.append({
            "id": definition["id"], "story_type": definition["story_type"], "priority": definition["priority"],
            "transaction_ids": definition["transaction_ids"], "manager_ids": definition["manager_ids"],
            "draft_evidence": definition.get("draft_picks", []),
            "relevant_seasons": relevant_seasons, "span": f"{relevant_seasons[0]}" if len(relevant_seasons) == 1 else f"{relevant_seasons[0]}–{relevant_seasons[-1]}",
            "headline": definition["headline"].format(**facts), "label": definition["label"].format(**facts),
            "context": definition["context"].format(**facts), "decision": definition["decision"].format(**facts),
            "aftermath": definition["aftermath"].format(**facts),
            "evidence": [item.format(**facts) for item in definition["evidence"]],
        })
    return sorted(stories, key=lambda story: -story["priority"])
