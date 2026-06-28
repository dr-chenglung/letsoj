import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings


class MaterialsTestBase(SimpleTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.override = override_settings(COURSE_MATERIALS_ROOT=str(self.root))
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self._tmp.cleanup)

    def write(self, rel, content=b"x"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p


class ServeFileTests(MaterialsTestBase):
    def test_pdf_served_inline(self):
        self.write("講義.pdf", b"%PDF-1.4 fake")
        resp = self.client.get("/materials/file", {"path": "講義.pdf"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Disposition"].startswith("inline"))
        self.assertIn("UTF-8''", resp["Content-Disposition"])

    def test_doc_served_as_attachment(self):
        self.write("作業.doc", b"fake")
        resp = self.client.get("/materials/file", {"path": "作業.doc"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Disposition"].startswith("attachment"))

    def test_path_traversal_returns_404(self):
        resp = self.client.get("/materials/file", {"path": "../settings.py"})
        self.assertEqual(resp.status_code, 404)

    def test_missing_file_returns_404(self):
        resp = self.client.get("/materials/file", {"path": "nope.pdf"})
        self.assertEqual(resp.status_code, 404)

    def test_directory_path_returns_404(self):
        (self.root / "sub").mkdir()
        resp = self.client.get("/materials/file", {"path": "sub"})
        self.assertEqual(resp.status_code, 404)
