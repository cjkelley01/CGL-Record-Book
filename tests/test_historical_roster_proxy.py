import unittest
from unittest.mock import patch

from scripts.compare_historical_roster_replay import compare
from scripts.historical_roster_proxy import cutoff_lineup_estimates


def row(week, pid, actual, *, team=1, slot=0):
    return {"season": "2025", "week": str(week), "team_id": str(team),
            "player_id": str(pid), "actual": str(actual),
            "actual_records": "1", "lineup_slot_id": str(slot),
            "eligible_slots": "[0]"}


class HistoricalRosterProxyTests(unittest.TestCase):
    @patch("scripts.compare_historical_roster_replay.summarize")
    @patch("scripts.compare_historical_roster_replay.replay")
    def test_comparison_keeps_only_successful_cutoffs_shared_by_both_models(self, replay, _):
        baseline = [{"season": 2025, "cutoff": 4}, {"season": 2025, "cutoff": 7}]
        proxy = [{"season": 2025, "cutoff": 7}, {"season": 2025, "cutoff": 10}]
        replay.side_effect = [(baseline, []), (proxy, [])]

        result, paired_baseline, paired_proxy = compare([], [], [])

        self.assertEqual(result["paired_cutoffs"], [(2025, 7)])
        self.assertEqual(paired_baseline, [baseline[1]])
        self.assertEqual(paired_proxy, [proxy[0]])

    def test_future_actuals_and_projections_cannot_affect_estimate(self):
        data = [row(1, 11, 10), row(2, 11, 20), row(3, 11, 30),
                row(4, 11, 999)]
        data[-1]["projected"] = "9999"
        a, _ = cutoff_lineup_estimates(data, 2025, 3, [1])
        self.assertEqual(a[1], 15)
        data[-1]["actual"] = "50000"
        data[-1]["projected"] = "1"
        b, _ = cutoff_lineup_estimates(data, 2025, 3, [1])
        self.assertEqual(a, b)

    def test_missing_eligible_starter_fails_closed(self):
        data = [row(1, 11, 10), row(2, 11, 20), row(3, 11, 30),
                row(3, 12, 5, slot=2)]
        result, coverage = cutoff_lineup_estimates(data, 2025, 3, [1])
        self.assertIsNone(result)
        self.assertEqual(coverage["teams_valid"], 0)

    def test_other_team_player_history_can_be_used_without_future_leakage(self):
        data = [row(1, 11, 10, team=2), row(2, 11, 20, team=2),
                row(3, 11, 30, team=1)]
        result, _ = cutoff_lineup_estimates(data, 2025, 3, [1])
        self.assertEqual(result[1], 15)


if __name__ == "__main__":
    unittest.main()
