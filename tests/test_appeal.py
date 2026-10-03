import os
import tempfile
import unittest
from unittest.mock import patch

from app import app
from submission_log import read_entries


class TestAppealEndpoint(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        app.config["SUBMISSION_LOG_PATH"] = os.path.join(self.tmpdir.name, "submissions.jsonl")
        app.config["APPEAL_LOG_PATH"] = os.path.join(self.tmpdir.name, "appeals.jsonl")
        llm_patcher = patch("app.llm_signal", return_value={"available": True, "label": "AI", "confidence": 0.9})
        llm_patcher.start()
        self.addCleanup(llm_patcher.stop)
        self.client = app.test_client()
        self.submission = self.client.post("/submit", json={"text": "hello", "creator_id": "u"}).get_json()

    def appeal(self, **body):
        return self.client.post("/appeal", json=body)

    def test_appeal_logs_with_original_and_sets_under_review(self):
        resp = self.appeal(content_id=self.submission["content_id"],
                           creator_reasoning="I wrote this myself", evidence="drafts.docx history")
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body["status"], "Under Review")
        # No automatic reclassification
        self.assertEqual(body["original_classification"]["attribution"], self.submission["label"])
        self.assertEqual(read_entries(app.config["APPEAL_LOG_PATH"]), [body])

    def test_rejects_invalid_requests(self):
        cid = self.submission["content_id"]
        self.assertEqual(self.appeal(creator_reasoning="x").status_code, 400)
        self.assertEqual(self.appeal(content_id=cid).status_code, 400)
        self.assertEqual(self.appeal(content_id="missing", creator_reasoning="x").status_code, 404)
        self.appeal(content_id=cid, creator_reasoning="x")
        self.assertEqual(self.appeal(content_id=cid, creator_reasoning="again").status_code, 409)


if __name__ == "__main__":
    unittest.main()
