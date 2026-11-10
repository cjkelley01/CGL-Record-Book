import copy
import unittest

from scripts.freeze_week9_history import freeze_week9_history


class FrozenWeek9HistoryTests(unittest.TestCase):
    def setUp(self):
        teams = [{"team_id": i, "team_name": f"T{i}"} for i in range(1, 15)]
        matches = []
        for week in range(1, 15):
            for i in range(1, 14, 2):
                matches.append({"matchup_id": 7 * (week - 1) + (i + 1) // 2,
                                "matchup_period": week, "stage": "regular_season",
                                "home_team_id": i, "away_team_id": i + 1,
                                "decided": week <= 8, "home_score": 90 if week <= 8 else 0,
                                "away_score": 80 if week <= 8 else 0, "winner": "HOME" if week <= 8 else "UNDECIDED"})
        self.history = {"seasons": [{"season": 2026, "teams": teams,
                                     "matchups": matches, "through_week": 8}]}
        self.espn = {"schedule": [{"id": m["matchup_id"], "matchupPeriodId": 9,
                                   "home": {"teamId": m["home_team_id"], "totalPoints": 110},
                                   "away": {"teamId": m["away_team_id"], "totalPoints": 100},
                                   "winner": "HOME"}
                                  for m in matches if m["matchup_period"] == 9]}

    def test_injects_only_week9_and_preserves_source(self):
        before = copy.deepcopy(self.history)
        frozen = freeze_week9_history(self.history, self.espn)
        games = frozen["seasons"][0]["matchups"]
        self.assertEqual(9, frozen["seasons"][0]["through_week"])
        self.assertEqual(7, sum(m["decided"] for m in games if m["matchup_period"] == 9))
        self.assertEqual(35, sum(not m["decided"] for m in games if m["matchup_period"] > 9))
        self.assertEqual(before, self.history)
        self.assertEqual(110.0, next(m for m in games if m["matchup_period"] == 9)["home_score"])

    def test_rejects_unfinished_espn_scores(self):
        self.espn["schedule"][0]["winner"] = "UNDECIDED"
        with self.assertRaisesRegex(ValueError, "not finalized"):
            freeze_week9_history(self.history, self.espn)

    def test_rejects_future_result_leakage(self):
        next(m for m in self.history["seasons"][0]["matchups"] if m["matchup_period"] == 10)["decided"] = True
        with self.assertRaisesRegex(ValueError, "undecided"):
            freeze_week9_history(self.history, self.espn)

    def test_rejects_schedule_mismatch(self):
        self.espn["schedule"][0]["away"]["teamId"] = 14
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            freeze_week9_history(self.history, self.espn)


if __name__ == "__main__":
    unittest.main()
