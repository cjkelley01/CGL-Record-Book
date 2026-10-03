import unittest
import json
from copy import deepcopy
from pathlib import Path

from scripts.moves_stories import build_stories, filter_stories, validate_unique_event_coverage


class MoveStoryTests(unittest.TestCase):
    def setUp(self):
        self.stories = [
            {"id": "single", "relevant_seasons": [2024], "label": "2024 story"},
            {"id": "career", "relevant_seasons": [2024, 2025], "label": "2024–2025 · Sustained success"},
            {"id": "later", "relevant_seasons": [2025], "label": "2025 story"},
        ]

    def test_all_time_keeps_every_curated_story(self):
        self.assertEqual(3, len(filter_stories(self.stories, None)))

    def test_year_filter_uses_supporting_event_seasons(self):
        self.assertEqual(["single", "career"], [story["id"] for story in filter_stories(self.stories, 2024)])
        self.assertEqual([], filter_stories(self.stories, 2026))

    def test_cross_year_story_keeps_full_span_label(self):
        story = next(story for story in filter_stories(self.stories, 2025) if story["id"] == "career")
        self.assertEqual("2024–2025 · Sustained success", story["label"])

    def test_duplicate_event_coverage_fails_validation(self):
        definitions = [
            {"id": "one", "transaction_ids": ["event"]},
            {"id": "two", "transaction_ids": ["event"]},
        ]
        with self.assertRaisesRegex(ValueError, "retold"):
            validate_unique_event_coverage(definitions)


class ArchivedStoryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((Path(__file__).resolve().parents[1] / "app/data/core_history.json").read_text())
        cls.moves = cls.archive["moves"]["transactions"]
        cls.seasons = cls.archive["seasons"]
        cls.stories = {s["id"]: s for s in build_stories(cls.moves, cls.seasons)}

    def test_brown_reversal_does_not_count_akers_as_a_success(self):
        story = self.stories["timberwolves-waiver-rhythm"]
        self.assertIn("3 days later", story["decision"])
        self.assertIn("413.2 points in 28 starts", story["aftermath"])
        self.assertIn("3 distinct acquisitions", story["evidence"])
        self.assertEqual(4, len(story["transaction_ids"]))
        self.assertEqual([2024, 2025], story["relevant_seasons"])

    def test_combined_deals_match_actual_playoff_result(self):
        story = self.stories["alex-double-deal-2024"]
        self.assertEqual(2, len(story["transaction_ids"]))
        self.assertIn("57.0 points", story["aftermath"])
        self.assertIn("139.4–145", story["aftermath"])
        self.assertIn("5.6 points short", story["aftermath"])
        self.assertEqual(16, story["draft_evidence"][0]["round"])

    def test_incorrect_draft_position_blocks_publication(self):
        seasons = deepcopy(self.seasons)
        pick = next(p for s in seasons if s["season"] == 2024 for p in s["draft_picks"]
                    if p["player_name"] == "Christian McCaffrey")
        pick["overall_pick"] = 2
        with self.assertRaisesRegex(ValueError, "draft evidence changed"):
            build_stories(self.moves, seasons)

    def test_missing_departure_blocks_second_chance_story(self):
        moves = [m for m in self.moves if m["id"] != "7b8164c4-32b9-4aba-bfc7-a02edd9bf066"]
        with self.assertRaisesRegex(ValueError, "missing supporting transactions"):
            build_stories(moves, self.seasons)

    def test_changed_playoff_participation_blocks_five_starter_claim(self):
        moves = deepcopy(self.moves)
        deal = next(m for m in moves if m["id"] == "0052ede9-4ab1-447b-b770-31c30f19186e")
        side = next(s for s in deal["sides"] if "alex_h" in s["manager_ids"])
        side["acquired"][0]["contribution"]["weekly"] = []
        with self.assertRaisesRegex(ValueError, "all five"):
            build_stories(moves, self.seasons)

    def test_published_stories_are_current(self):
        self.assertEqual(self.archive["moves"]["stories"], build_stories(self.moves, self.seasons))


if __name__ == "__main__":
    unittest.main()

