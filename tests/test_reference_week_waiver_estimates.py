"""Cross-week waiver estimates must remain schedule-aware and reproducible."""
import unittest

from scripts.analytics.espn_projections import waiver_replacements


def free_agent(pid, pro_team, score, week=10):
    return {
        "status": "FREEAGENT",
        "onTeamId": 0,
        "player": {
            "id": pid,
            "proTeamId": pro_team,
            "eligibleSlots": [0],
            "stats": [{"statSourceId": 1, "scoringPeriodId": week,
                       "appliedTotal": score}],
        },
    }


class ReferenceWeekWaiverTests(unittest.TestCase):
    def test_uses_top_three_verified_options_with_target_week_games(self):
        pool = [free_agent(101, 1, 24), free_agent(102, 2, 18),
                free_agent(103, 3, 12), free_agent(104, 4, 6)]
        result = waiver_replacements(pool, 11, set(), [0], {1, 2, 3},
                                     projection_week=10)
        self.assertEqual(1, len(result))
        self.assertEqual(18, result[0]["projection"])

    def test_refuses_bye_candidates_even_if_reference_projection_positive(self):
        pool = [free_agent(101, 1, 24), free_agent(102, 2, 18),
                free_agent(103, 3, 12)]
        self.assertEqual([], waiver_replacements(
            pool, 11, set(), [0], {1, 2}, projection_week=10))

    def test_refuses_crossweek_estimate_without_verified_schedule(self):
        pool = [free_agent(101, 1, 24), free_agent(102, 2, 18),
                free_agent(103, 3, 12)]
        self.assertEqual([], waiver_replacements(
            pool, 11, set(), [0], projection_week=10))

    def test_refuses_unrostered_status_ambiguity(self):
        pool = [free_agent(101, 1, 24), free_agent(102, 2, 18),
                free_agent(103, 3, 12)]
        pool[0]["status"] = "ONTEAM"
        self.assertEqual([], waiver_replacements(
            pool, 11, set(), [0], {1, 2, 3}, projection_week=10))


if __name__ == "__main__":
    unittest.main()
