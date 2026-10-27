import json
import tempfile
import unittest
from pathlib import Path

from scripts.analytics.espn_projections import (
    extract_weekly_means, projection_for_week, starter_slots, normalized_players, waiver_replacements,
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

    def test_bye_player_skipped_and_eligible_bench_player_used(self):
        from scripts.analytics.optimal_lineup import optimize_lineup
        missing = player(11, 0)
        missing["playerPoolEntry"]["player"]["stats"] = []
        bench = player(12, 14)
        self.assertEqual(
            optimize_lineup(normalized_players([missing, bench], 9, skip_missing=True), [0])["projected_points"],
            14,
        )
        with self.assertRaises(ValueError):
            optimize_lineup(normalized_players([missing], 9, skip_missing=True), [0])

    def test_ed_week_nine_defense_on_bye_does_not_count_as_valid(self):
        from scripts.analytics.optimal_lineup import optimize_lineup
        bye_defense = player(99, 0, week=9, slots=[16])
        with self.assertRaises(ValueError):
            optimize_lineup(normalized_players([bye_defense], 9, skip_missing=True), [16])
        replacement = player(100, 7, week=9, slots=[16])
        result = optimize_lineup(normalized_players([bye_defense, replacement], 9, skip_missing=True), [16])
        self.assertEqual(result["projected_points"], 7)

    def test_waiver_replacement_requires_confirmed_availability(self):
        pool = []
        for pid, score in enumerate([18, 15, 12, 9], start=100):
            entry = {"status": "FREEAGENT", "onTeamId": 0,
                     "player": {"id": pid, "eligibleSlots": [0],
                                "stats": [{"statSourceId": 1, "scoringPeriodId": 9,
                                           "appliedTotal": score}]}}
            pool.append(entry)
        selected = waiver_replacements(pool, 9, set(), [0])
        self.assertEqual(selected[0]["projection"], 15)
        self.assertEqual(waiver_replacements(pool[:2], 9, set(), [0]), [])
        pool[2]["onTeamId"] = 5
        self.assertEqual(waiver_replacements(pool, 9, {103}, [0]), [])

    def test_multiple_waiver_replacements_for_same_position(self):
        pool = [{"status": "FREEAGENT", "onTeamId": 0,
                 "player": {"id": pid, "eligibleSlots": [2],
                            "stats": [{"statSourceId": 1, "scoringPeriodId": 9,
                                       "appliedTotal": score}]}}
                for pid, score in [(101, 18), (102, 15), (103, 12)]]
        selected = waiver_replacements(pool, 9, set(), [2, 2])
        self.assertEqual(len(selected), 2)
        self.assertEqual(len({p["player_id"] for p in selected}), 2)
        self.assertTrue(all(p["projection"] == 15 for p in selected))

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
