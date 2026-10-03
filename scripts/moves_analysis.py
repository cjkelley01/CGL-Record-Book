"""Normalize ESPN moves and measure points actually placed in starting lineups."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


BENCH_SLOTS = {20, 21}
COMPLETED_STATUS = "EXECUTED"
ACQUISITION_ITEMS = {"ADD", "TRADE"}
MOVE_TYPES = {"WAIVER", "FREEAGENT", "TRADE_ACCEPT"}

THRESHOLDS = {
    "waiver_gold": {"points": 100.0, "starts": 6},
    "got_away": {"points": 80.0, "starts": 5},
    "deal_maker": {"points": 100.0, "starts": 6},
    "buyer_remorse": {"received_max": 35.0, "surrendered_min": 100.0},
    "championship_reinforcement": {"playoff_points": 25.0, "playoff_starts": 2},
    "turning_point": {"points": 120.0, "starts": 7, "potential_swings": 1},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def deduplicate_transactions(cards: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Player cards repeat a transaction once per involved player; keep one copy by ID."""
    by_id: dict[str, dict[str, Any]] = {}
    references = 0
    for card in cards:
        for transaction in card.get("transactions", []):
            references += 1
            transaction_id = transaction.get("id")
            if transaction_id:
                by_id.setdefault(str(transaction_id), transaction)
    rows = sorted(
        by_id.values(),
        key=lambda row: (row.get("processDate") or row.get("proposedDate") or 0, str(row.get("id"))),
    )
    return rows, references - len(rows)


def merge_recent_transactions(
    archived: list[dict[str, Any]], recent_payload: dict[str, Any]
) -> list[dict[str, Any]]:
    """Merge the recent league view without allowing a partial copy to overwrite detail."""
    by_id = {str(row["id"]): row for row in archived if row.get("id")}
    for row in recent_payload.get("transactions", []):
        key = str(row.get("id", ""))
        if key and key not in by_id:
            by_id[key] = row
    return sorted(by_id.values(), key=lambda row: (row.get("proposedDate") or 0, str(row.get("id"))))


def is_complete_move(transaction: dict[str, Any]) -> bool:
    """Only executed acquisitions qualify; trades must retain both sides and every asset."""
    if transaction.get("status") != COMPLETED_STATUS or transaction.get("type") not in MOVE_TYPES:
        return False
    items = transaction.get("items", [])
    if transaction.get("type") != "TRADE_ACCEPT":
        return any(item.get("type") == "ADD" and item.get("toTeamId") for item in items)
    trade_items = [item for item in items if item.get("type") == "TRADE"]
    from_teams = {int(item["fromTeamId"]) for item in trade_items if item.get("fromTeamId")}
    to_teams = {int(item["toTeamId"]) for item in trade_items if item.get("toTeamId")}
    return len(from_teams) >= 2 and from_teams == to_teams and all(
        item.get("playerId") is not None and item.get("fromTeamId") and item.get("toTeamId") for item in trade_items
    )


def weekly_player_rows(data_root: Path, season: int) -> list[dict[str, Any]]:
    """Read exact scoring-period stats; appliedStatTotal can be multiweek cumulative."""
    rows: list[dict[str, Any]] = []
    for path in sorted((data_root / "raw" / str(season) / "weeks").glob("*/mRoster.json")):
        week = int(path.parent.name)
        payload = read_json(path)
        for team in payload.get("teams", []):
            for entry in team.get("roster", {}).get("entries", []):
                pool = entry.get("playerPoolEntry", {})
                player = pool.get("player", {})
                actual = scoring_period_total(player, week, 0) or 0.0
                projected = scoring_period_total(player, week, 1)
                rows.append({
                    "week": week,
                    "team_id": int(team["id"]),
                    "player_id": int(entry["playerId"]),
                    "player_name": player.get("fullName") or str(entry["playerId"]),
                    "position": player.get("defaultPositionId"),
                    "eligible_slots": player.get("eligibleSlots", []),
                    "lineup_slot_id": int(entry.get("lineupSlotId", 20)),
                    "started": int(entry.get("lineupSlotId", 20)) not in BENCH_SLOTS,
                    "points": round(float(actual or 0), 2),
                    "projected_points": round(float(projected), 2) if projected is not None else None,
                })
    return rows


def scoring_period_total(player: dict[str, Any], week: int, source: int) -> float | None:
    """Return one NFL week's stat, never ESPN's cumulative matchup total."""
    value = next((stat.get("appliedTotal") for stat in player.get("stats", [])
                  if stat.get("scoringPeriodId") == week and stat.get("statSourceId") == source), None)
    return float(value) if value is not None else None


def transaction_date(row: dict[str, Any]) -> str | None:
    millis = row.get("processDate") or row.get("proposedDate")
    if not millis:
        return None
    return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).date().isoformat()


def stage_for_week(week: int, team_id: int, regular_periods: int, matchup_by_week: dict[tuple[int, int], str]) -> str:
    if week <= regular_periods:
        return "regular_season"
    return matchup_by_week.get((team_id, week), "consolation")


def matchup_stage_by_week(season: dict[str, Any]) -> dict[tuple[int, int], str]:
    result: dict[tuple[int, int], str] = {}
    for matchup in season["matchups"]:
        for week in matchup["scoring_periods"]:
            for team_id in (matchup.get("home_team_id"), matchup.get("away_team_id")):
                if team_id is not None:
                    result[(int(team_id), int(week))] = matchup["stage"]
    return result


def ownership_bounds(transactions: list[dict[str, Any]]) -> dict[tuple[str, int, int], int | None]:
    """Map each acquisition item to its next departure, preserving reacquisition episodes."""
    events: dict[tuple[int, int], list[tuple[int, int, str, str]]] = defaultdict(list)
    for tx in transactions:
        if tx.get("status") != COMPLETED_STATUS:
            continue
        week = int(tx.get("scoringPeriodId") or 0)
        stamp = int(tx.get("processDate") or tx.get("proposedDate") or 0)
        for item in tx.get("items", []):
            player = item.get("playerId")
            if player is None:
                continue
            if item.get("type") in ACQUISITION_ITEMS and item.get("toTeamId"):
                events[(int(item["toTeamId"]), int(player))].append((week, stamp, "in", str(tx["id"])))
            if item.get("type") in {"DROP", "TRADE"} and item.get("fromTeamId"):
                events[(int(item["fromTeamId"]), int(player))].append((week, stamp, "out", str(tx["id"])))
    bounds: dict[tuple[str, int, int], int | None] = {}
    for (team, player), player_events in events.items():
        ordered = sorted(player_events, key=lambda event: (event[1], event[2] == "in"))
        for index, event in enumerate(ordered):
            if event[2] != "in":
                continue
            departure = next((later[0] for later in ordered[index + 1:] if later[2] == "out"), None)
            bounds[(event[3], team, player)] = departure
    return bounds


def player_contribution(
    weekly: list[dict[str, Any]], team_id: int, player_id: int, start_week: int,
    end_week: int | None, regular_periods: int, stages: dict[tuple[int, int], str],
) -> dict[str, Any]:
    evidence = []
    for row in weekly:
        if row["team_id"] != team_id or row["player_id"] != player_id or not row["started"]:
            continue
        if row["week"] < start_week or (end_week is not None and row["week"] >= end_week):
            continue
        stage = stage_for_week(row["week"], team_id, regular_periods, stages)
        if stage == "consolation":
            continue
        evidence.append({"week": row["week"], "stage": stage, "points": row["points"]})
    regular = [row for row in evidence if row["stage"] == "regular_season"]
    playoffs = [row for row in evidence if row["stage"] == "championship_playoffs"]
    return {
        "regular_points": round(sum(row["points"] for row in regular), 2),
        "regular_starts": len(regular),
        "playoff_points": round(sum(row["points"] for row in playoffs), 2),
        "playoff_starts": len(playoffs),
        "total_points": round(sum(row["points"] for row in evidence), 2),
        "total_starts": len(evidence),
        "weekly": evidence,
    }


def combine_metrics(players: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ("regular_points", "regular_starts", "playoff_points", "playoff_starts", "total_points", "total_starts")
    return {field: round(sum(player["contribution"][field] for player in players), 2) for field in fields}


def projected_alternative(
    weekly: list[dict[str, Any]], acquired: dict[str, Any], week: int, team_id: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    candidates = [row for row in weekly if row["week"] == week and row["team_id"] == team_id
                  and not row["started"] and row["lineup_slot_id"] == 20
                  and acquired["lineup_slot_id"] in row.get("eligible_slots", [])
                  and row["projected_points"] is not None]
    candidates.sort(key=lambda row: (-row["projected_points"], row["player_name"]))
    return (candidates[0] if candidates else None), candidates[:3]


def counterfactual_summary(
    move: dict[str, Any], weekly: list[dict[str, Any]], season: dict[str, Any]
) -> dict[str, Any]:
    matchup_for_team_week: dict[tuple[int, int], dict[str, Any]] = {}
    for matchup in season["matchups"]:
        if matchup["stage"] == "consolation":
            continue
        for week in matchup["scoring_periods"]:
            for side, other in (("home", "away"), ("away", "home")):
                team_id = matchup.get(f"{side}_team_id")
                if team_id is not None:
                    matchup_for_team_week[(int(team_id), int(week))] = {
                        "result": "W" if matchup.get("winner") == side.upper() else "L",
                        "margin": abs(float(matchup.get("home_score") or 0) - float(matchup.get("away_score") or 0)),
                        "opponent": matchup.get(f"{other}_team_name"),
                        "stage": matchup["stage"],
                    }
    comparisons = []
    for side in move["sides"]:
        team_id = side["team_id"]
        for player in side["acquired"]:
            acquired_rows = [row for row in weekly if row["team_id"] == team_id and row["player_id"] == player["player_id"]]
            for evidence in player["contribution"]["weekly"]:
                current = next((row for row in acquired_rows if row["week"] == evidence["week"]), None)
                matchup = matchup_for_team_week.get((team_id, evidence["week"]))
                if not current or not matchup or matchup["result"] != "W":
                    continue
                alternative, sensitivity = projected_alternative(weekly, current, evidence["week"], team_id)
                if not alternative:
                    continue
                delta = round(current["points"] - alternative["points"], 2)
                swings = delta > matchup["margin"]
                sensitivity_swings = [round(current["points"] - candidate["points"], 2) > matchup["margin"] for candidate in sensitivity]
                comparisons.append({
                    "week": evidence["week"], "team_id": team_id, "opponent": matchup["opponent"],
                    "acquired_player": player["player_name"], "actual_points": current["points"],
                    "alternative": alternative["player_name"], "alternative_actual_points": alternative["points"],
                    "alternative_projected_points": alternative["projected_points"], "matchup_margin": matchup["margin"],
                    "potentially_swung": swings, "robust_across_top_three": bool(sensitivity_swings) and all(sensitivity_swings),
                })
    return {
        "potential_swings": sum(row["potentially_swung"] for row in comparisons),
        "robust_swings": sum(row["potentially_swung"] and row["robust_across_top_three"] for row in comparisons),
        "comparisons": comparisons,
        "method": "Replaces an acquired starter with the eligible bench player carrying the highest archived pregame projection; actual alternative points determine whether the recorded winning margin changes.",
    }


def build_moves(
    data_root: Path,
    seasons: list[dict[str, Any]],
    manager_lookup: Callable[[int, int, str], list[str]],
    manager_name_lookup: Callable[[list[str]], list[str]],
    player_catalog_factory: Callable[[Path, int], dict[int, dict[str, Any]]],
) -> dict[str, Any]:
    all_moves: list[dict[str, Any]] = []
    coverage = []
    team_context: dict[tuple[int, int], dict[str, Any]] = {}
    for season in seasons:
        year = season["season"]
        for team in season["teams"]:
            team_context[(year, team["team_id"])] = team
        cards_path = data_root / "raw" / str(year) / "transactions" / "kona_playercard.json"
        cards = read_json(cards_path) if cards_path.exists() else []
        transactions, duplicate_refs = deduplicate_transactions(cards)
        recent_path = data_root / "raw" / str(year) / "league" / "mTransactions2.json"
        recent = read_json(recent_path) if recent_path.exists() else {}
        transactions = merge_recent_transactions(transactions, recent)
        completed = [row for row in transactions if row.get("status") == COMPLETED_STATUS]
        catalog = player_catalog_factory(data_root, year)
        weekly = weekly_player_rows(data_root, year)
        stages = matchup_stage_by_week(season)
        bounds = ownership_bounds(completed)
        team_by_id = {team["team_id"]: team for team in season["teams"]}

        for transaction in completed:
            if not is_complete_move(transaction):
                continue
            acquired_items = [item for item in transaction.get("items", []) if item.get("type") in ACQUISITION_ITEMS and item.get("toTeamId")]
            if not acquired_items:
                continue
            week = int(transaction.get("scoringPeriodId") or 0)
            side_ids = sorted({int(item["toTeamId"]) for item in acquired_items})
            sides = []
            for team_id in side_ids:
                team = team_by_id.get(team_id)
                if not team:
                    continue
                acquired = []
                for item in acquired_items:
                    if int(item["toTeamId"]) != team_id:
                        continue
                    player_id = int(item["playerId"])
                    end = bounds.get((str(transaction["id"]), team_id, player_id))
                    meta = catalog.get(player_id, {})
                    acquired.append({
                        "player_id": player_id,
                        "player_name": meta.get("player_name", str(player_id)),
                        "position": meta.get("position") or meta.get("default_position_id"),
                        "contribution": player_contribution(weekly, team_id, player_id, week, end,
                                                            season["settings"]["regular_season_matchup_periods"], stages),
                    })
                outgoing_items = [item for item in transaction.get("items", [])
                                  if item.get("fromTeamId") == team_id and item.get("type") in {"DROP", "TRADE"}]
                outgoing = [{"player_id": int(item["playerId"]),
                             "player_name": catalog.get(int(item["playerId"]), {}).get("player_name", str(item["playerId"]))}
                            for item in outgoing_items]
                ids = team["manager_ids"] or manager_lookup(year, team_id, team["team_name"])
                sides.append({"team_id": team_id, "team_name": team["team_name"], "manager_ids": ids,
                              "manager_names": manager_name_lookup(ids), "acquired": acquired, "outgoing": outgoing,
                              "contribution": combine_metrics(acquired)})
            if not sides:
                continue
            move = {"id": str(transaction["id"]), "season": year,
                    "kind": "trade" if transaction.get("type") == "TRADE_ACCEPT" else transaction.get("type", "").lower(),
                    "status": "completed", "date": transaction_date(transaction), "week": week, "sides": sides,
                    "badges": [], "counterfactual": None}
            all_moves.append(move)

        feed_files = list((data_root / "raw" / str(year) / "transactions").glob("kona_league_communication_*.json"))
        feed_topics = 0
        for path in feed_files:
            payload = read_json(path)
            feed_topics += len(payload.get("communication", {}).get("topics", [])) if isinstance(payload, dict) else 0
        coverage.append({"season": year, "player_cards": len(cards), "unique_transactions": len(transactions),
                         "completed_transactions": len(completed), "duplicate_player_card_references_removed": duplicate_refs,
                         "activity_feed_topics": feed_topics,
                         "limitations": "Player cards expose completed transactions only; rejected, canceled, and failed historical moves are unavailable."})

        for move in [row for row in all_moves if row["season"] == year]:
            move["counterfactual"] = counterfactual_summary(move, weekly, season)

    # Link drops to the next acquisition of that player by a different team.
    acquisitions_by_player: dict[tuple[int, int], list[tuple[int, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for move in all_moves:
        for side in move["sides"]:
            for player in side["acquired"]:
                acquisitions_by_player[(move["season"], player["player_id"])].append((move["week"], move, side))
    for move in all_moves:
        for side in move["sides"]:
            for outgoing in side["outgoing"]:
                later = [entry for entry in acquisitions_by_player[(move["season"], outgoing["player_id"])]
                         if entry[0] >= move["week"] and entry[2]["team_id"] != side["team_id"]]
                if later:
                    _, next_move, next_side = sorted(later, key=lambda entry: entry[0])[0]
                    contribution = next((player["contribution"] for player in next_side["acquired"]
                                         if player["player_id"] == outgoing["player_id"]), None)
                    if contribution:
                        outgoing["subsequent_team"] = next_side["team_name"]
                        outgoing["subsequent_contribution"] = contribution
                        outgoing["next_move_id"] = next_move["id"]

    for move in all_moves:
        total = combine_metrics([player for side in move["sides"] for player in side["acquired"]])
        if move["kind"] in {"waiver", "freeagent"} and total["regular_points"] >= THRESHOLDS["waiver_gold"]["points"] and total["regular_starts"] >= THRESHOLDS["waiver_gold"]["starts"]:
            move["badges"].append("waiver_gold")
        if any(out.get("subsequent_contribution", {}).get("total_points", 0) >= THRESHOLDS["got_away"]["points"]
               and out.get("subsequent_contribution", {}).get("total_starts", 0) >= THRESHOLDS["got_away"]["starts"]
               for side in move["sides"] for out in side["outgoing"]):
            move["badges"].append("got_away")
        if move["kind"] == "trade" and any(side["contribution"]["total_points"] >= THRESHOLDS["deal_maker"]["points"]
                                            and side["contribution"]["total_starts"] >= THRESHOLDS["deal_maker"]["starts"] for side in move["sides"]):
            move["badges"].append("deal_maker")
        if move["kind"] == "trade" and len(move["sides"]) > 1 and any(
            side["contribution"]["total_points"] <= THRESHOLDS["buyer_remorse"]["received_max"] and
            sum(other["contribution"]["total_points"] for other in move["sides"] if other is not side) >= THRESHOLDS["buyer_remorse"]["surrendered_min"]
            for side in move["sides"]):
            move["badges"].append("buyer_remorse")
        if total["playoff_points"] >= THRESHOLDS["championship_reinforcement"]["playoff_points"] and total["playoff_starts"] >= THRESHOLDS["championship_reinforcement"]["playoff_starts"]:
            move["badges"].append("championship_reinforcement")
        if total["total_points"] >= THRESHOLDS["turning_point"]["points"] and total["total_starts"] >= THRESHOLDS["turning_point"]["starts"] and move["counterfactual"]["potential_swings"] >= THRESHOLDS["turning_point"]["potential_swings"]:
            move["badges"].append("turning_point")

    front_office: dict[str, dict[str, Any]] = {}
    for move in all_moves:
        for side in move["sides"]:
            for manager_id, manager_name in zip(side["manager_ids"], side["manager_names"]):
                row = front_office.setdefault(manager_id, {"manager_id": manager_id, "manager_name": manager_name,
                    "transaction_volume": 0, "waiver_hits": [], "trade_hits": [], "playoff_hits": [], "seasons": set()})
                row["transaction_volume"] += 1
                row["seasons"].add(move["season"])
                if "waiver_gold" in move["badges"] and move["kind"] != "trade": row["waiver_hits"].append(move["id"])
                if "deal_maker" in move["badges"] and move["kind"] == "trade": row["trade_hits"].append(move["id"])
                if "championship_reinforcement" in move["badges"]: row["playoff_hits"].append(move["id"])
    front_rows = []
    for row in front_office.values():
        row["seasons"] = sorted(row["seasons"])
        row["badges"] = []
        if len(set(row["waiver_hits"])) >= 2: row["badges"].append("waiver_whisperer")
        if len(set(row["trade_hits"])) >= 2: row["badges"].append("deal_architect")
        if len(set(row["playoff_hits"])) >= 2: row["badges"].append("playoff_acquirer")
        if row["badges"]: front_rows.append(row)

    distributions = {
        "pickup_regular_points": sorted(round(combine_metrics([p for s in move["sides"] for p in s["acquired"]])["regular_points"], 2)
                                        for move in all_moves if move["kind"] in {"waiver", "freeagent"}),
        "trade_side_points": sorted(side["contribution"]["total_points"] for move in all_moves if move["kind"] == "trade" for side in move["sides"]),
    }
    return {
        "coverage": coverage,
        "thresholds": THRESHOLDS,
        "threshold_policy": "Fixed qualification floors selected after inspecting the full observed distributions; categories are hidden when no move qualifies.",
        "counterfactual_limitations": "Comparisons use archived projections only when an eligible bench alternative exists. They do not remodel injuries, later transactions, changed seeding, or an alternate playoff bracket, and move-level swings must not be added together.",
        "distributions": distributions,
        "transactions": sorted(all_moves, key=lambda move: (move["season"], move["week"], move["date"] or ""), reverse=True),
        "front_office": sorted(front_rows, key=lambda row: (-len(row["badges"]), -len(row["waiver_hits"]) - len(row["trade_hits"]), row["manager_name"])),
    }
