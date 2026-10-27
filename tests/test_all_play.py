import unittest

from scripts.analytics.all_play import calculate_all_play


def season(games, teams=4):
    return {"season": 2026, "teams": [
        {"team_id": i, "team_name": f"Team {i}"} for i in range(1, teams + 1)
    ], "matchups": games}


def game(week, home, away, hs, aws, decided=True):
    return {"stage": "regular_season", "decided": decided,
            "matchup_period": week, "home_team_id": home, "away_team_id": away,
            "home_score": hs, "away_score": aws}


class AllPlayTests(unittest.TestCase):
    def test_all_play_expected_wins_and_luck(self):
        result = calculate_all_play(season([
            game(1, 1, 2, 110, 100), game(1, 3, 4, 90, 80)
        ]))
        rows = {r["team_id"]: r for r in result["teams"]}
        self.assertEqual([1], result["completed_weeks"])
        self.assertEqual(3, rows[1]["all_play_wins"])
        self.assertEqual(1, rows[1]["expected_wins"])
        self.assertEqual(0, rows[1]["luck_differential"])
        self.assertEqual(0, rows[4]["expected_wins"])
        self.assertEqual(0.6667, rows[3]["luck_differential"])

    def test_ties_count_half(self):
        result = calculate_all_play(season([
            game(1, 1, 2, 100, 100), game(1, 3, 4, 90, 80)
        ]))
        rows = {r["team_id"]: r for r in result["teams"]}
        self.assertEqual(2, rows[1]["all_play_wins"])
        self.assertEqual(1, rows[1]["all_play_ties"])
        self.assertEqual(0.8333, rows[1]["expected_wins"])
        self.assertEqual(-0.3333, rows[1]["luck_differential"])

    def test_partial_and_live_weeks_are_excluded(self):
        result = calculate_all_play(season([
            game(1, 1, 2, 100, 90), game(1, 3, 4, 80, 70),
            game(2, 1, 2, 110, 105), game(2, 3, 4, 95, 90, decided=False)
        ]))
        self.assertEqual([1], result["completed_weeks"])
        self.assertTrue(all(r["weeks"] == 1 for r in result["teams"]))

    def test_duplicate_scores_rejected(self):
        with self.assertRaises(ValueError):
            calculate_all_play(season([
                game(1, 1, 2, 100, 90), game(1, 1, 3, 100, 80)
            ]))


if __name__ == "__main__":
    unittest.main()
