import unittest

from scripts.analytics.power_rankings import calculate_power_rankings
from tests.test_all_play import game, season


class PowerRankingsTests(unittest.TestCase):
    def test_weekly_ranking_and_rank_movement(self):
        result = calculate_power_rankings(season([
            game(1, 1, 2, 140, 100), game(1, 3, 4, 90, 80),
            game(2, 1, 2, 70, 100), game(2, 3, 4, 150, 80),
        ]))
        self.assertEqual([1, 2], result["completed_weeks"])
        self.assertEqual(1, result["weekly_rankings"][0]["teams"][0]["team_id"])
        self.assertEqual(2, len(result["weekly_rankings"]))
        for snapshot in result["weekly_rankings"]:
            self.assertEqual([1, 2, 3, 4], sorted(row["rank"] for row in snapshot["teams"]))
            self.assertTrue(all(0 <= row["power_score"] <= 100 for row in snapshot["teams"]))
        self.assertTrue(all(row["rank_change"] is None for row in result["weekly_rankings"][0]["teams"]))
        self.assertTrue(all(row["rank_change"] is not None for row in result["weekly_rankings"][1]["teams"]))

    def test_partial_week_does_not_count(self):
        result = calculate_power_rankings(season([
            game(1, 1, 2, 100, 90), game(1, 3, 4, 80, 70),
            game(2, 1, 2, 120, 90), game(2, 3, 4, 100, 70, decided=False),
        ]))
        self.assertEqual([1], result["completed_weeks"])

    def test_no_complete_weeks(self):
        result = calculate_power_rankings(season([]))
        self.assertEqual([], result["weekly_rankings"])

    def test_duplicate_scores_rejected(self):
        with self.assertRaises(ValueError):
            calculate_power_rankings(season([
                game(1, 1, 2, 100, 90), game(1, 1, 3, 100, 80),
            ]))


if __name__ == "__main__":
    unittest.main()
