import unittest

from scripts.moves_stories import filter_stories, validate_unique_event_coverage


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


if __name__ == "__main__":
    unittest.main()
