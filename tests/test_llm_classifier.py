import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from signals.llm_classifier import llm_signal


def fake_client(content=None, error=None):
    """A stand-in for the Groq client that returns `content` or raises `error`."""
    client = MagicMock()
    if error:
        client.chat.completions.create.side_effect = error
    else:
        message = SimpleNamespace(content=content)
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=message)]
        )
    return client


class TestLlmSignal(unittest.TestCase):
    def test_parses_ai_label(self):
        result = llm_signal("text", client=fake_client('{"label": "AI", "confidence": 0.85}'))
        self.assertEqual(result, {"available": True, "label": "AI", "confidence": 0.85})

    def test_parses_human_label_case_insensitively(self):
        result = llm_signal("text", client=fake_client('{"label": "human", "confidence": 0.7}'))
        self.assertEqual(result["label"], "Human")

    def test_clamps_confidence_to_0_1(self):
        result = llm_signal("text", client=fake_client('{"label": "AI", "confidence": 1.7}'))
        self.assertEqual(result["confidence"], 1.0)

    def test_passage_is_sent_inside_delimiters(self):
        client = fake_client('{"label": "AI", "confidence": 0.5}')
        llm_signal("my passage", client=client)
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(messages[1]["content"], "<passage>\nmy passage\n</passage>")

    def test_unavailable_on_api_error(self):
        result = llm_signal("text", client=fake_client(error=RuntimeError("rate limited")))
        self.assertFalse(result["available"])
        self.assertIsNone(result["label"])

    def test_unavailable_on_malformed_output(self):
        for bad in ("not json", '{"label": "Maybe", "confidence": 0.5}', '{"label": "AI"}'):
            result = llm_signal("text", client=fake_client(bad))
            self.assertFalse(result["available"], bad)


if __name__ == "__main__":
    unittest.main()
