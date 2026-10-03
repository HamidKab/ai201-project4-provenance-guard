import unittest

from app import app


class TestSubmitEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

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
