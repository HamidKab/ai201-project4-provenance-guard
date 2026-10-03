import unittest

from scoring import confidence_score, label_for


def ucw(percent):
    return {"ucw_percent": percent}


def llm(label, confidence=0.9):
    return {"available": True, "label": label, "confidence": confidence}


UNAVAILABLE = {"available": False, "label": None, "confidence": None}


class TestConfidenceScore(unittest.TestCase):
    def test_high_ucw_and_llm_ai_is_likely_ai(self):
        score = confidence_score(ucw(0.08), llm("AI"))
        self.assertEqual(label_for(score), "Likely AI")

    def test_low_ucw_and_llm_human_is_likely_human(self):
        score = confidence_score(ucw(0.0), llm("Human"))
        self.assertEqual(label_for(score), "Likely Human")

    def test_high_ucw_but_llm_human_leans_human(self):
        # Planning: a human can write with many uncommon words (e.g. poetry)
        score = confidence_score(ucw(0.08), llm("Human"))
        self.assertLess(score, 0.5)
        self.assertEqual(label_for(score), "Likely Human")

    def test_low_ucw_but_llm_ai_leans_ai(self):
        # Planning: people edit generated text to sound natural
        score = confidence_score(ucw(0.0), llm("AI"))
        self.assertGreater(score, 0.5)

    def test_llm_unavailable_is_always_uncertain(self):
        for percent in (0.0, 0.03, 0.5):
            score = confidence_score(ucw(percent), UNAVAILABLE)
            self.assertEqual(label_for(score), "Uncertain", percent)

    def test_score_stays_in_0_1(self):
        for label in ("AI", "Human"):
            for conf in (0.0, 1.0):
                for percent in (0.0, 1.0):
                    score = confidence_score(ucw(percent), llm(label, conf))
                    self.assertGreaterEqual(score, 0.0)
                    self.assertLessEqual(score, 1.0)


class TestLabelFor(unittest.TestCase):
    def test_point_six_is_not_enough_for_likely_ai(self):
        self.assertEqual(label_for(0.6), "Uncertain")

    def test_boundaries(self):
        self.assertEqual(label_for(0.70), "Likely AI")
        self.assertEqual(label_for(0.69), "Uncertain")
        self.assertEqual(label_for(0.35), "Likely Human")
        self.assertEqual(label_for(0.36), "Uncertain")


if __name__ == "__main__":
    unittest.main()
