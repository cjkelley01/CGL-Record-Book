import unittest

from scripts.moves_analysis import (
    deduplicate_transactions,
    is_complete_move,
    ownership_bounds,
    player_contribution,
    scoring_period_total,
    side_success_flags,
    got_away_qualifies,
    counterfactual_summary,
    projected_alternative,
)


class MovesAnalysisTests(unittest.TestCase):
    def test_duplicate_transactions_are_one_deal(self):
        trade = {"id": "deal", "status": "EXECUTED", "type": "TRADE_ACCEPT", "items": []}
        rows, duplicates = deduplicate_transactions([{"transactions": [trade]}, {"transactions": [trade]}])
        self.assertEqual(["deal"], [row["id"] for row in rows])
        self.assertEqual(1, duplicates)

    def test_incomplete_or_unexecuted_trade_is_not_complete(self):
        partial = {"id": "x", "status": "EXECUTED", "type": "TRADE_ACCEPT", "items": [
            {"type": "TRADE", "playerId": 1, "fromTeamId": 1, "toTeamId": 2}
        ]}
        pending = {**partial, "status": "PENDING"}
        self.assertFalse(is_complete_move(partial))
        self.assertFalse(is_complete_move(pending))

    def test_reacquisition_creates_separate_ownership_stints(self):
        transactions = [
            {"id": "add1", "status": "EXECUTED", "scoringPeriodId": 2, "processDate": 20, "items": [{"type": "ADD", "playerId": 7, "toTeamId": 1}]},
            {"id": "drop", "status": "EXECUTED", "scoringPeriodId": 4, "processDate": 40, "items": [{"type": "DROP", "playerId": 7, "fromTeamId": 1}]},
            {"id": "add2", "status": "EXECUTED", "scoringPeriodId": 6, "processDate": 60, "items": [{"type": "ADD", "playerId": 7, "toTeamId": 1}]},
        ]
        bounds = ownership_bounds(transactions)
        self.assertEqual(4, bounds[("add1", 1, 7)])
        self.assertIsNone(bounds[("add2", 1, 7)])

    def test_only_starter_points_inside_stint_count(self):
        weekly = [
            {"week": 1, "team_id": 1, "player_id": 7, "started": True, "points": 20},
            {"week": 2, "team_id": 1, "player_id": 7, "started": False, "points": 30},
            {"week": 3, "team_id": 1, "player_id": 7, "started": True, "points": 10},
            {"week": 4, "team_id": 1, "player_id": 7, "started": True, "points": 40},
        ]
        result = player_contribution(weekly, 1, 7, 2, 4, 3, {})
        self.assertEqual(10, result["total_points"])
        self.assertEqual(1, result["total_starts"])

    def test_multiweek_matchup_uses_exact_week_stat_not_cumulative_total(self):
        player = {"appliedStatTotal": 93.16, "stats": [
            {"scoringPeriodId": 14, "statSourceId": 0, "appliedTotal": 51.88},
            {"scoringPeriodId": 15, "statSourceId": 0, "appliedTotal": 41.28},
        ]}
        self.assertEqual(41.28, scoring_period_total(player, 15, 0))

    def test_multi_player_trade_counts_as_one_transaction(self):
        trade = {"id": "deal", "status": "EXECUTED", "type": "TRADE_ACCEPT", "items": [
            {"type": "TRADE", "playerId": 1, "fromTeamId": 1, "toTeamId": 2},
            {"type": "TRADE", "playerId": 2, "fromTeamId": 1, "toTeamId": 2},
            {"type": "TRADE", "playerId": 3, "fromTeamId": 2, "toTeamId": 1},
        ]}
        self.assertTrue(is_complete_move(trade))
        rows, _ = deduplicate_transactions([{"transactions": [trade, trade, trade]}])
        self.assertEqual(1, len(rows))

    def test_trade_success_is_attributed_per_side(self):
        move = {"kind": "trade"}
        strong = {"contribution": {"regular_points": 120, "regular_starts": 7, "total_points": 120,
                                    "total_starts": 7, "playoff_points": 0, "playoff_starts": 0}}
        weak = {"contribution": {"regular_points": 20, "regular_starts": 2, "total_points": 20,
                                  "total_starts": 2, "playoff_points": 0, "playoff_starts": 0}}
        self.assertTrue(side_success_flags(move, strong)["trade"])
        self.assertFalse(side_success_flags(move, weak)["trade"])

    def test_got_away_requires_an_actual_drop(self):
        contribution = {"total_points": 120, "total_starts": 7}
        self.assertTrue(got_away_qualifies({"departure_type": "drop", "subsequent_contribution": contribution}))
        self.assertFalse(got_away_qualifies({"departure_type": "trade", "subsequent_contribution": contribution}))

    def test_zero_projection_is_not_a_plausible_alternative(self):
        acquired = {"lineup_slot_id": 0}
        weekly = [{"week": 3, "team_id": 1, "started": False, "lineup_slot_id": 20,
                   "eligible_slots": [0], "projected_points": 0, "points": 0, "player_name": "Unavailable"}]
        alternative, sensitivity = projected_alternative(weekly, acquired, 3, 1)
        self.assertIsNone(alternative)
        self.assertEqual([], sensitivity)

    def test_multi_player_multiweek_comparison_counts_one_series(self):
        move = {"kind": "freeagent", "sides": [{"team_id": 1, "acquired": [
            {"player_id": 7, "player_name": "A", "contribution": {"weekly": [{"week": 15}, {"week": 16}]}},
            {"player_id": 8, "player_name": "B", "contribution": {"weekly": [{"week": 15}, {"week": 16}]}},
        ]}]}
        weekly = []
        for week in (15, 16):
            weekly.extend([
                {"week": week, "team_id": 1, "player_id": 7, "player_name": "A", "started": True,
                 "lineup_slot_id": 0, "eligible_slots": [0], "projected_points": 20, "points": 30},
                {"week": week, "team_id": 1, "player_id": 8, "player_name": "B", "started": True,
                 "lineup_slot_id": 2, "eligible_slots": [2], "projected_points": 18, "points": 25},
                {"week": week, "team_id": 1, "player_id": 9, "player_name": "Bench QB", "started": False,
                 "lineup_slot_id": 20, "eligible_slots": [0], "projected_points": 10, "points": 15},
                {"week": week, "team_id": 1, "player_id": 10, "player_name": "Bench RB", "started": False,
                 "lineup_slot_id": 20, "eligible_slots": [2], "projected_points": 9, "points": 12},
            ])
        season = {"matchups": [{"matchup_id": 44, "stage": "championship_playoffs", "scoring_periods": [15, 16],
                                 "home_team_id": 1, "away_team_id": 2, "home_team_name": "One", "away_team_name": "Two",
                                 "home_score": 200, "away_score": 180, "winner": "HOME"}]}
        summary = counterfactual_summary(move, weekly, season)
        self.assertEqual(1, len(summary["comparisons"]))
        self.assertEqual(1, summary["potential_swings"])


if __name__ == "__main__":
    unittest.main()
