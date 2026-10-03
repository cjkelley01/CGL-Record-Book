import unittest

from scripts.moves_analysis import (
    deduplicate_transactions,
    is_complete_move,
    ownership_bounds,
    player_contribution,
    scoring_period_total,
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


if __name__ == "__main__":
    unittest.main()
