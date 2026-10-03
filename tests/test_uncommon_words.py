import unittest

from signals.uncommon_words import ucw_signal

AI_TEXT = (
    "Let's delve into the intricate tapestry of modern cuisine. This vibrant "
    "realm is a testament to culinary creativity, and it underscores the "
    "pivotal role of tradition in fostering a seamless, holistic experience."
)

HUMAN_TEXT = (
    "I went to the store yesterday and grabbed some bread and milk. The line "
    "was long so I ended up chatting with the guy behind me about the game."
)


class TestUcwSignal(unittest.TestCase):
    def test_ai_style_text_crosses_threshold(self):
        result = ucw_signal(AI_TEXT)
        self.assertTrue(result["above_threshold"])
        self.assertGreater(result["ucw_percent"], 0.03)
        self.assertIn("delve", result["matched_words"])

    def test_casual_human_text_stays_below_threshold(self):
        result = ucw_signal(HUMAN_TEXT)
        self.assertFalse(result["above_threshold"])
        self.assertEqual(result["uncommon_count"], 0)
        self.assertEqual(result["ucw_percent"], 0.0)

    def test_ratio_is_uncommon_over_total(self):
        # 2 uncommon words ("delve", "realm") out of 4 total
        result = ucw_signal("Delve into realm now")
        self.assertEqual(result["total_words"], 4)
        self.assertEqual(result["uncommon_count"], 2)
        self.assertEqual(result["ucw_percent"], 0.5)

    def test_matching_ignores_case_and_punctuation(self):
        result = ucw_signal("DELVE! Tapestry, realm.")
        self.assertEqual(result["uncommon_count"], 3)

    def test_empty_or_wordless_text_returns_zero(self):
        for text in ("", "   ", "123 !!! ..."):
            result = ucw_signal(text)
            self.assertEqual(result["total_words"], 0)
            self.assertEqual(result["ucw_percent"], 0.0)
            self.assertFalse(result["above_threshold"])

    def test_custom_threshold(self):
        # 1 of 10 words = 10%
        text = "delve one two three four five six seven eight nine"
        self.assertTrue(ucw_signal(text, threshold=0.05)["above_threshold"])
        self.assertFalse(ucw_signal(text, threshold=0.2)["above_threshold"])


if __name__ == "__main__":
    unittest.main()
