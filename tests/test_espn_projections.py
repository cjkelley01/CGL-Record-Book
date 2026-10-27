import json
import tempfile
import unittest
from pathlib import Path

from scripts.analytics.espn_projections import (
    extract_weekly_means, projection_for_week, starter_slots,
)


def player(pid, points, week=9, slots=None):
    return {"playerPoolEntry": {"player": {
        "id": pid, "eligibleSlots": slots or [0],
        "stats": [{"statSourceId": 1, "scoringPeriodId": week, "appliedTotal": points}],
    }}}


class EspnProjectionsTests(unittest.TestCase):
    def test_starting_slots_include_flex_not_bench(self):
        settings = {"settings": {"rosterSettings": {
            "lineupSlotCounts": {"0": 1, "2": 2, "23": 1, "20": 6, "21": 1}}}}
        self.assertEqual([0, 2, 2, 23], starter_slots(settings))

    def test_only_exact_week_projected_stats(self):
        p = {"stats": [
            {"statSourceId": 0, "scoringPeriodId": 9, "appliedTotal": 50},
            {"statSourceId": 1, "scoringPeriodId": 9, "appliedTotal": 12},
            {"statSourceId": 1, "scoringPeriodId": 10, "appliedTotal": 15},
        ]}
        self.assertEqual(12, projection_for_week(p, 9))
        with self.assertRaises(ValueError):
            projection_for_week(p, 11)

    def test_complete_week_and_missing_future_week(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw" / "2026"
            (root / "league").mkdir(parents=True)
            (root / "weeks" / "09").mkdir(parents=True)
            (root / "league" / "mSettings.json").write_text(json.dumps({
                "settings": {"rosterSettings": {"lineupSlotCounts": {"0": 1, "20": 4}}}
            }))
            (root / "weeks" / "09" / "mRoster.json").write_text(json.dumps({
                "teams": [{"id": 1, "roster": {"entries": [player(11, 19)]}},
                          {"id": 2, "roster": {"entries": [player(21, 17)]}}]
            }))
            result = extract_weekly_means(directory, 2026, [9, 10], [1, 2])
            self.assertEqual(19, result["means"][1][9])
            self.assertFalse(result["ready"])
            self.assertEqual("missing_file", result["coverage"][1]["status"])


if __name__ == "__main__":
    unittest.main()
