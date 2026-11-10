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

    def test_fixed_bracket_does_not_reseed_after_upset(self):
        teams = [{"team_id": i, "team_name": f"Team {i}"} for i in range(1, 7)]
        # Distinct standings points lock in seeds #1 through #6.
        season = {"season": 2026, "teams": teams, "matchups": [
            {"stage": "regular_season", "decided": True, "matchup_period": 1,
             "home_team_id": 1, "away_team_id": 6,
             "home_score": 160, "away_score": 110},
            {"stage": "regular_season", "decided": True, "matchup_period": 1,
             "home_team_id": 2, "away_team_id": 5,
             "home_score": 150, "away_score": 120},
            {"stage": "regular_season", "decided": True, "matchup_period": 1,
             "home_team_id": 3, "away_team_id": 4,
             "home_score": 140, "away_score": 130},
        ]}
        # With no variance, #6 upsets #3 and #4 beats #5.
        # Fixed bracket: #1 faces #4 (loses), #2 faces #6 (wins).
        # Reseeding would instead pair #1 vs #6 and #2 vs #4.
        means = {i: {15: 0, 16: 0, 17: 0, 18: 0} for i in range(1, 7)}
        means[6][15], means[4][15] = 100, 100
        means[4][16], means[2][16] = 100, 100
        means[2][17], means[2][18] = 100, 100
        result = simulate(season, means, trials=1, seed=3, deviation=0.000001)
        by_id = {t["team_id"]: t for t in result["teams"]}
        self.assertEqual(by_id[4]["final_probability"], 1)
        self.assertEqual(by_id[2]["final_probability"], 1)
        self.assertEqual(by_id[1]["final_probability"], 0)

    def test_missing_projection_fails_closed(self):
        with self.assertRaises(ValueError):
            simulate(sample(), {}, trials=10)


if __name__ == "__main__":
    unittest.main()
