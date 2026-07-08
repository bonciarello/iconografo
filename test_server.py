"""Test suite for Iconografo Flask backend."""

import json
import unittest
import sys
import os

# Add parent dir to path so we can import server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app, gallery


class IconografoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def setUp(self):
        gallery.clear()

    # ── Page serving ──────────────────────────────────────────────────

    def test_index_returns_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.content_type)
        self.assertIn(b"Iconografo", resp.data)

    # ── Robots & Sitemap ──────────────────────────────────────────────

    def test_robots_txt(self):
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"User-agent", resp.data)
        self.assertIn(b"Sitemap:", resp.data)

    def test_sitemap_xml(self):
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"urlset", resp.data)
        self.assertIn(b"cristianporco.it", resp.data)

    # ── Gallery API ───────────────────────────────────────────────────

    def test_list_empty_gallery(self):
        resp = self.client.get("/api/icons")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data, [])

    def test_save_and_list_icon(self):
        png_b64 = "data:image/png;base64,iVBORw0KGgo="
        resp = self.client.post(
            "/api/icons",
            data=json.dumps({"word": "cane", "variant": 0, "data": png_b64}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        saved = json.loads(resp.data)
        self.assertIn("id", saved)
        self.assertEqual(saved["word"], "cane")
        self.assertEqual(saved["variant"], 0)
        self.assertEqual(saved["data"], png_b64)

        # List
        resp2 = self.client.get("/api/icons")
        self.assertEqual(resp2.status_code, 200)
        data2 = json.loads(resp2.data)
        self.assertEqual(len(data2), 1)
        self.assertEqual(data2[0]["id"], saved["id"])

    def test_save_multiple_icons(self):
        png = "data:image/png;base64,AAA="
        for i in range(5):
            resp = self.client.post(
                "/api/icons",
                data=json.dumps({"word": f"test-{i}", "variant": i, "data": png}),
                content_type="application/json",
            )
            self.assertEqual(resp.status_code, 201)

        resp = self.client.get("/api/icons")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 5)

    def test_save_missing_word(self):
        resp = self.client.post(
            "/api/icons",
            data=json.dumps({"data": "data:image/png;base64,AAA="}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        err = json.loads(resp.data)
        self.assertIn("error", err)

    def test_save_missing_data(self):
        resp = self.client.post(
            "/api/icons",
            data=json.dumps({"word": "test"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_save_empty_body(self):
        resp = self.client.post("/api/icons", data="bad", content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_save_invalid_png_prefix(self):
        resp = self.client.post(
            "/api/icons",
            data=json.dumps({"word": "x", "data": "not-a-png"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_gallery_order_newest_first(self):
        png = "data:image/png;base64,BBB="
        self.client.post("/api/icons", data=json.dumps({"word": "a", "variant": 0, "data": png}), content_type="application/json")
        import time
        time.sleep(0.01)
        self.client.post("/api/icons", data=json.dumps({"word": "z", "variant": 1, "data": png}), content_type="application/json")

        resp = self.client.get("/api/icons")
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        # newest first: "z" should come before "a"
        self.assertEqual(data[0]["word"], "z")

    # ── Gallery limit ─────────────────────────────────────────────────

    def test_gallery_limit_100(self):
        png = "data:image/png;base64,CCC="
        for i in range(120):
            self.client.post("/api/icons", data=json.dumps({"word": f"w{i}", "variant": 0, "data": png}), content_type="application/json")
        resp = self.client.get("/api/icons")
        data = json.loads(resp.data)
        self.assertLessEqual(len(data), 50)  # API returns max 50


if __name__ == "__main__":
    unittest.main(verbosity=2)
