import unittest
from scripts.historical_roster_proxy import cutoff_lineup_estimates


def row(week, pid, actual, *, team=1, slot=0):
    return {"season": "2025", "week": str(week), "team_id": str(team),
            "player_id": str(pid), "actual": str(actual),
            "actual_records": "1", "lineup_slot_id": str(slot),
            "eligible_slots": "[0]"}


class HistoricalRosterProxyTests(unittest.TestCase):
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
