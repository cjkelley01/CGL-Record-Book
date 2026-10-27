import unittest

from scripts.analytics.playoff_simulator import simulate_regular_season


def season():
    return {"season": 2026, "teams": [
        {"team_id": i, "team_name": f"Team {i}"} for i in range(1, 15)
    ], "matchups": [
        {"stage": "regular_season", "decided": False, "matchup_period": 9,
         "home_team_id": i, "away_team_id": i + 1}
        for i in range(1, 15, 2)
    ]}


class PlayoffSimulatorTests(unittest.TestCase):
    def test_reproducible_and_probabilities(self):
        means = {i: {9: 100 + i} for i in range(1, 15)}
        a = simulate_regular_season(season(), means, simulations=100, seed=12)
        b = simulate_regular_season(season(), means, simulations=100, seed=12)
        self.assertEqual(a, b)
        self.assertAlmostEqual(sum(t["playoff_probability"] for t in a["teams"]), 6, places=3)
        self.assertAlmostEqual(sum(t["bye_probability"] for t in a["teams"]), 2, places=3)

    def test_missing_future_projection_rejected(self):
        with self.assertRaises(ValueError):
            simulate_regular_season(season(), {}, simulations=10)

    def test_invalid_simulation_count(self):
        with self.assertRaises(ValueError):
            simulate_regular_season(season(), {}, simulations=0)


if __name__ == "__main__":
    unittest.main()
