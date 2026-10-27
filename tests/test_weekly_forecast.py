import unittest

from scripts.analytics.weekly_forecast import historical_means, blended_means, simulate


def sample():
    teams = [{"team_id": i, "team_name": f"Team {i}"} for i in range(1, 15)]
    matches = []
    for i in range(1, 15, 2):
        matches.append({"stage": "regular_season", "decided": True,
                        "matchup_period": 1, "home_team_id": i,
                        "away_team_id": i + 1, "home_score": 100 + i,
                        "away_score": 100 + i + 1})
        matches.append({"stage": "regular_season", "decided": False,
                        "matchup_period": 9, "home_team_id": i,
                        "away_team_id": i + 1})
    return {"season": 2026, "teams": teams, "matchups": matches}


class WeeklyForecastTests(unittest.TestCase):
    def test_historical_and_blended(self):
        season = sample()
        history = historical_means(season, [9, 15, 16, 17, 18])
        self.assertEqual(history[1][9], 101)
        self.assertEqual(blended_means(history, history), history)

    def test_probabilities_and_bracket(self):
        season = sample()
        means = historical_means(season, [9, 15, 16, 17, 18])
        result = simulate(season, means, trials=200, seed=4)
        self.assertEqual(result, simulate(season, means, trials=200, seed=4))
        self.assertAlmostEqual(sum(t["playoff_probability"] for t in result["teams"]), 6, places=2)
        self.assertAlmostEqual(sum(t["bye_probability"] for t in result["teams"]), 2, places=2)
        self.assertAlmostEqual(sum(t["championship_probability"] for t in result["teams"]), 1, places=2)
        self.assertAlmostEqual(sum(t["final_probability"] for t in result["teams"]), 2, places=2)

    def test_missing_projection_fails_closed(self):
        with self.assertRaises(ValueError):
            simulate(sample(), {}, trials=10)


if __name__ == "__main__":
    unittest.main()
