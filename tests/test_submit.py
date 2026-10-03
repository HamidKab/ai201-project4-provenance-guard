import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from app import app, limiter
from submission_log import read_entries

FAKE_LLM = {"available": True, "label": "AI", "confidence": 0.9}


class TestSubmitEndpoint(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmpdir.name, "submissions.jsonl")
        app.config["SUBMISSION_LOG_PATH"] = self.log_path
        self.client = app.test_client()
        llm_patcher = patch("app.llm_signal", return_value=FAKE_LLM)
        llm_patcher.start()
        self.addCleanup(llm_patcher.stop)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_response_and_log_include_llm_signal_and_score(self):
        body = self.client.post("/submit", json={"text": "hello", "creator_id": "u"}).get_json()
        self.assertEqual(body["signals"]["llm"], FAKE_LLM)
        # LLM says AI at 0.9, UCW 0 -> 0.75 * 0.9 = 0.675
        self.assertEqual(body["confidence"], 0.675)
        self.assertEqual(body["label"], "Uncertain")
        entry = read_entries(self.log_path)[0]
        self.assertEqual(entry["signal_2_llm_label"], "AI")
        self.assertEqual(entry["signal_2_llm_confidence"], 0.9)

    def test_submission_writes_structured_log_entry(self):
        resp = self.client.post("/submit", json={
            "text": "Let's delve into this tapestry.",
            "creator_id": "user-123",
        })
        body = resp.get_json()
        entries = read_entries(self.log_path)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["content_id"], body["content_id"])
        self.assertEqual(entry["creator_id"], "user-123")
        self.assertEqual(entry["attribution"], body["label"])
        self.assertEqual(entry["signal_1_ucw_percent"], body["signals"]["ucw"]["ucw_percent"])
        datetime.fromisoformat(entry["timestamp"])  # raises if malformed

    def test_each_submission_gets_unique_content_id_and_log_line(self):
        for _ in range(3):
            self.client.post("/submit", json={"text": "hello there", "creator_id": "u"})
        entries = read_entries(self.log_path)
        self.assertEqual(len(entries), 3)
        self.assertEqual(len({e["content_id"] for e in entries}), 3)

    def test_rate_limited_after_5_per_minute(self):
        limiter.enabled = True
        limiter.reset()
        self.addCleanup(setattr, limiter, "enabled", False)
        codes = [self.client.post("/submit", json={"text": "hi", "creator_id": "u"}).status_code
                 for _ in range(6)]
        self.assertEqual(codes, [200] * 5 + [429])

    def test_rejected_submission_is_not_logged(self):
        self.client.post("/submit", json={"creator_id": "u"})
        self.assertEqual(read_entries(self.log_path), [])

    def test_valid_submission_returns_label_and_ucw_signal(self):
        resp = self.client.post("/submit", json={
            "text": "Let's delve into this tapestry.",
            "creator_id": "user-123",
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["creator_id"], "user-123")
        self.assertIn(body["label"], {"Likely AI", "Uncertain", "Likely Human"})
        self.assertIn("ucw", body["signals"])
        self.assertEqual(body["signals"]["ucw"]["uncommon_count"], 2)

    def test_missing_text_returns_400(self):
        resp = self.client.post("/submit", json={"creator_id": "user-123"})
        self.assertEqual(resp.status_code, 400)

    def test_missing_creator_id_returns_400(self):
        resp = self.client.post("/submit", json={"text": "hello"})
        self.assertEqual(resp.status_code, 400)

    def test_blank_text_returns_400(self):
        resp = self.client.post("/submit", json={"text": "   ", "creator_id": "u"})
        self.assertEqual(resp.status_code, 400)

    def test_non_json_body_returns_400(self):
        resp = self.client.post("/submit", data="not json", content_type="text/plain")
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
