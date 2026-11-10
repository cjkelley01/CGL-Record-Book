import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.export_remaining_week_projections import build_report


class RemainingWeekExportTests(unittest.TestCase):
    def test_missing_projection_is_null_and_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw/2026/league"
            path.mkdir(parents=True)
            path.joinpath("mTeam.json").write_text(json.dumps({
                "teams": [{"id": i, "name": f"Team {i}"} for i in range(1, 15)]
            }))
            means = {i: {10: float(i)} for i in range(1, 15)}
            del means[2][10]
            audit = {i: ({10: {"method": "roster_only", "starters": []}} if i != 2 else {})
                     for i in range(1, 15)}
            mock = {"means": means, "lineup_audit": audit,
                    "optimized_means": means, "optimized_audit": audit, "ready": False, "coverage": [{
                "week": 10, "status": "incomplete", "teams_with_valid_lineups": 13,
                "teams_expected": 14, "teams_without_valid_lineups": [{"team_id": 2, "reason": "no legal lineup"}],
            }]}
            with patch("scripts.export_remaining_week_projections.extract_weekly_means", return_value=mock):
                result = build_report(Path(tmp), weeks=[10])
            self.assertFalse(result["ready"])
            self.assertIsNone(result["teams"][1]["projected_points"]["10"])
            self.assertEqual(13, result["coverage"][0]["valid_lineups"])
            self.assertEqual(0.0, result["teams"][0]["full_optimization_uplift"]["10"])
            self.assertIsNone(result["teams"][1]["full_optimization_projected_points"]["10"])
            self.assertIsNone(result["teams"][1]["lineup_audit"]["10"])
            self.assertEqual("roster_only", result["teams"][0]["lineup_audit"]["10"]["method"])

    def test_rejects_incomplete_league(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw/2026/league"
            path.mkdir(parents=True)
            path.joinpath("mTeam.json").write_text('{"teams":[{"id":1,"name":"Only team"}]}')
            with self.assertRaises(ValueError):
                build_report(Path(tmp), weeks=[10])


if __name__ == "__main__":
    unittest.main()
