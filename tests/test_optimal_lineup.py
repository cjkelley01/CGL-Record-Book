import unittest
from scripts.analytics.optimal_lineup import optimize_lineup


class OptimalLineupTests(unittest.TestCase):
    def test_preservation_fills_only_missing_slots_while_upside_replaces_starters(self):
        roster = [
            {"player_id": 1, "projection": 5, "eligible_slots": [17]},
            {"player_id": 2, "projection": 10, "eligible_slots": [23]},
        ]
        waiver = [
            {"player_id": -1001, "projection": 8, "eligible_slots": [6],
             "hypothetical_waiver": True},
            {"player_id": -1002, "projection": 11, "eligible_slots": [17],
             "hypothetical_waiver": True},
            {"player_id": -1003, "projection": 15, "eligible_slots": [23],
             "hypothetical_waiver": True},
        ]
        baseline = optimize_lineup(roster + waiver, [17, 23, 6],
                                   prefer_rostered=True)
        upside = optimize_lineup(roster + waiver, [17, 23, 6])
        self.assertEqual({1, 2, -1001},
                         {p["player_id"] for p in baseline["lineup"]})
        self.assertEqual({-1001, -1002, -1003},
                         {p["player_id"] for p in upside["lineup"]})
        self.assertEqual(23, baseline["projected_points"])
        self.assertEqual(34, upside["projected_points"])

    def test_flex_and_bench_compete_for_best_legal_lineup(self):
        players = [
            {"player_id": 1, "projection": 20, "eligible_slots": [2, 23]},
            {"player_id": 2, "projection": 19, "eligible_slots": [2, 23]},
            {"player_id": 3, "projection": 18, "eligible_slots": [4, 23]},
            {"player_id": 4, "projection": 30, "eligible_slots": [4, 23]},
        ]
        result = optimize_lineup(players, [2, 4, 23])
        self.assertEqual(69, result["projected_points"])
        self.assertEqual(3, len({p["player_id"] for p in result["lineup"]}))

    def test_injured_player_excluded(self):
        players = [
            {"player_id": 1, "projection": 30, "eligible_slots": [2], "available": False},
            {"player_id": 2, "projection": 12, "eligible_slots": [2]},
        ]
        self.assertEqual(12, optimize_lineup(players, [2])["projected_points"])

    def test_missing_projection_not_zero(self):
        with self.assertRaisesRegex(ValueError, "Missing projection"):
            optimize_lineup([{"player_id": 1, "eligible_slots": [2]}], [2])

    def test_no_legal_lineup(self):
        with self.assertRaisesRegex(ValueError, "No legal lineup"):
            optimize_lineup([
                {"player_id": 1, "projection": 20, "eligible_slots": [2]},
                {"player_id": 2, "projection": 19, "eligible_slots": [2]},
            ], [2, 4])

    def test_repeated_positions(self):
        result = optimize_lineup([
            {"player_id": 1, "projection": 10, "eligible_slots": [4]},
            {"player_id": 2, "projection": 15, "eligible_slots": [4]},
            {"player_id": 3, "projection": 20, "eligible_slots": [4]},
        ], [4, 4])
        self.assertEqual(35, result["projected_points"])


if __name__ == "__main__":
    unittest.main()
