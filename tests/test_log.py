import os
import tempfile
import unittest
from unittest.mock import patch

from app import app


class TestLogEndpoint(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        app.config["SUBMISSION_LOG_PATH"] = os.path.join(self.tmpdir.name, "submissions.jsonl")
        self.client = app.test_client()
        llm_patcher = patch("app.llm_signal", return_value={"available": True, "label": "Human", "confidence": 0.8})
        llm_patcher.start()
        self.addCleanup(llm_patcher.stop)

    def tearDown(self):
        self.tmpdir.cleanup()

    def submit(self, creator_id):
        return self.client.post("/submit", json={"text": "hello", "creator_id": creator_id}).get_json()

    def test_empty_log_returns_no_entries(self):
        resp = self.client.get("/log")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"count": 0, "entries": []})

    def test_returns_entries_newest_first(self):
        ids = [self.submit(f"user-{i}")["content_id"] for i in range(3)]
        body = self.client.get("/log").get_json()
        self.assertEqual(body["count"], 3)
        self.assertEqual([e["content_id"] for e in body["entries"]], ids[::-1])

    def test_limit_returns_most_recent_n(self):
        ids = [self.submit(f"user-{i}")["content_id"] for i in range(5)]
        body = self.client.get("/log?limit=2").get_json()
        self.assertEqual([e["content_id"] for e in body["entries"]], [ids[4], ids[3]])

    def test_entries_contain_audit_fields(self):
        self.submit("user-1")
        entry = self.client.get("/log").get_json()["entries"][0]
        for field in ("timestamp", "content_id", "attribution", "signal_1_ucw_percent"):
            self.assertIn(field, entry)

    def test_invalid_limit_returns_400(self):
        for bad in ("0", "-3", "abc"):
            resp = self.client.get(f"/log?limit={bad}")
            self.assertEqual(resp.status_code, 400, bad)


if __name__ == "__main__":
    unittest.main()
