import unittest
from scripts.audit_historical_availability import stat_summary, summarize_roster


class HistoricalAvailabilityAuditTests(unittest.TestCase):
    def test_projection_counts_are_not_claimed_point_in_time(self):
        player = {"stats": [
            {"statSourceId": 1, "statSplitTypeId": 1, "scoringPeriodId": 10, "appliedTotal": 12.5},
            {"statSourceId": 0, "statSplitTypeId": 1, "scoringPeriodId": 10, "appliedTotal": 18.0}
        ]}
        self.assertEqual(stat_summary(player, 10), 1)
        self.assertEqual(stat_summary(player, 9), 0)

    def test_missing_and_duplicate_projection_records_are_distinguished(self):
        projection = {"statSourceId": 1, "statSplitTypeId": 1,
                      "scoringPeriodId": 10, "appliedTotal": 12.5}
        payload = {"teams": [{"id": 1, "roster": {"entries": [
            {"playerId": 11, "playerPoolEntry": {"player": {"id": 11, "stats": [projection]}}},
            {"playerId": 12, "playerPoolEntry": {"player": {"id": 12, "stats": []}}},
            {"playerId": 13, "playerPoolEntry": {"player": {"id": 13, "stats": [projection, projection]}}}
        ]}}]}
        counts, sets = summarize_roster(payload, 10)
        self.assertEqual(counts["target_week_projection_present"], 1)
        self.assertEqual(counts["target_week_projection_missing"], 1)
        self.assertEqual(counts["target_week_projection_ambiguous"], 1)
        self.assertEqual(sets[1], {11, 12, 13})


if __name__ == "__main__":
    unittest.main()
