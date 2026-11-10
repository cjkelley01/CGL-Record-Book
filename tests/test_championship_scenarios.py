import unittest
from scripts.export_week9_championship_scenarios import build_championship_scenarios


class ChampionshipScenarioTests(unittest.TestCase):
    def setUp(self):
        teams = [{"team_id": i, "team_name": f"T{i}"} for i in range(1, 15)]
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

    def test_six_scenarios_and_probability_conservation(self):
        report = build_championship_scenarios(self.history, self.projections,
                                               simulations=40, seed=3)
        self.assertEqual(6, len(report["scenarios"]))
        for model in report["scenarios"].values():
            self.assertAlmostEqual(sum(t["championship_probability"] for t in model["teams"]), 1, places=2)
            self.assertAlmostEqual(sum(t["final_probability"] for t in model["teams"]), 2, places=2)
            self.assertAlmostEqual(sum(t["playoff_probability"] for t in model["teams"]), 6, places=2)

    def test_missing_week14_projection_is_not_imputed(self):
        self.projections["teams"][0]["projected_points"]["14"] = None
        with self.assertRaisesRegex(ValueError, "Week 14"):
            build_championship_scenarios(self.history, self.projections, simulations=10)

    def test_no_week10_result_leakage(self):
        self.history["seasons"][0]["matchups"][-1]["decided"] = True
        with self.assertRaisesRegex(ValueError, "Weeks 10-14"):
            build_championship_scenarios(self.history, self.projections, simulations=10)


if __name__ == "__main__":
    unittest.main()
