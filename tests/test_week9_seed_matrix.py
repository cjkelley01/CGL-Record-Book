import unittest
from unittest.mock import patch

from scripts.export_week9_seed_matrix import build_matrices


class Week9MatrixTests(unittest.TestCase):
    def setUp(self):
        teams = [{"team_id": i, "team_name": f"Team {i}"} for i in range(1, 15)]
        matchups = []
        for week in range(1, 15):
            for i in range(1, 14, 2):
                matchups.append({"stage": "regular_season", "matchup_period": week,
                                 "home_team_id": i, "away_team_id": i + 1,
                                 "decided": week < 10,
                                 "home_score": 100 if week < 10 else None,
                                 "away_score": 90 if week < 10 else None})
        self.history = {"seasons": [{"season": 2026, "teams": teams, "matchups": matchups}]}
        self.projections = {"ready": True, "weeks": list(range(10, 15)),
                            "baseline_policy": "roster_preservation",
                            "comparison_policy": "full_waiver_optimization",
                            "teams": [{"team_id": i,
                                       "projected_points": {str(w): 100 for w in range(10, 15)},
                                       "full_optimization_projected_points": {str(w): 110 for w in range(10, 15)}}
                                      for i in range(1, 15)]}

    def test_both_models_and_seed_consistency(self):
        result = build_matrices(self.history, self.projections, simulations=100, seed=1)
        self.assertEqual(set(result["models"]),
                         {"roster_preservation", "full_waiver_optimization"})
        for model in result["models"].values():
            for team in model["teams"]:
                probs = team["seed_probabilities"]
                self.assertAlmostEqual(sum(probs.values()), 1, places=2)
                self.assertAlmostEqual(sum(probs.get(str(i), 0) for i in range(1, 7)),
                                       team["playoff_probability"], places=2)

    def test_missing_projection_fails_closed(self):
        self.projections["teams"][0]["projected_points"]["10"] = None
        with self.assertRaises(ValueError):
            build_matrices(self.history, self.projections, simulations=10)

    def test_refuses_unfrozen_history(self):
        self.history["seasons"][0]["matchups"][0]["matchup_period"] = 10
        with self.assertRaises(ValueError):
            build_matrices(self.history, self.projections, simulations=10)


if __name__ == "__main__":
    unittest.main()
