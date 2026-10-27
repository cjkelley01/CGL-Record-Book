import unittest

from scripts.analytics.schedule_luck import calculate_schedule_luck
from tests.test_all_play import game, season


class ScheduleLuckTests(unittest.TestCase):
    def test_opponent_points_and_schedule_swap(self):
        result = calculate_schedule_luck(season([
            game(1, 1, 2, 110, 100),
            game(1, 3, 4, 90, 80),
        ]))
        rows = {row["team_id"]: row for row in result["teams"]}
        self.assertEqual([1], result["completed_weeks"])
        self.assertEqual(100, rows[1]["points_against_per_week"])
        self.assertEqual(2, rows[1]["average_opponent_weekly_rank"])
        self.assertEqual(1, rows[1]["actual_wins"])
        self.assertEqual(1, rows[1]["average_schedule_wins"])
        self.assertEqual(0, rows[1]["schedule_luck"])
        self.assertEqual(4, len(rows[1]["schedule_swap"]))

    def test_partial_week_excluded(self):
        result = calculate_schedule_luck(season([
            game(1, 1, 2, 100, 90), game(1, 3, 4, 80, 70),
            game(2, 1, 2, 110, 100), game(2, 3, 4, 90, 80, decided=False),
        ]))
        self.assertEqual([1], result["completed_weeks"])
        self.assertTrue(all(row["weeks"] == 1 for row in result["teams"]))

    def test_tied_scores_count_half(self):
        result = calculate_schedule_luck(season([
            game(1, 1, 2, 100, 100), game(1, 3, 4, 80, 70),
        ]))
        row = next(row for row in result["teams"] if row["team_id"] == 1)
        self.assertEqual(0.5, row["actual_wins"])

    def test_duplicate_week_rejected(self):
        with self.assertRaises(ValueError):
            calculate_schedule_luck(season([
                game(1, 1, 2, 100, 90), game(1, 1, 3, 100, 80),
            ]))


if __name__ == "__main__":
    unittest.main()
