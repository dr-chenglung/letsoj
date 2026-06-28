import tempfile
from pathlib import Path

from django.http import Http404
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from app_materials.views import resolve_within_root


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

    def file_url(self, rel):
        return reverse("materials_file", args=[rel])


class ServeFileTests(MaterialsTestBase):
    def test_pdf_served_inline(self):
        self.write("講義.pdf", b"%PDF-1.4 fake")
        resp = self.client.get(self.file_url("講義.pdf"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Disposition"].startswith("inline"))
        self.assertIn("UTF-8''", resp["Content-Disposition"])

    def test_doc_served_as_attachment(self):
        self.write("作業.doc", b"fake")
        resp = self.client.get(self.file_url("作業.doc"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Disposition"].startswith("attachment"))

    def test_path_traversal_raises_404(self):
        with self.assertRaises(Http404):
            resolve_within_root("../settings.py")

    def test_missing_file_returns_404(self):
        resp = self.client.get(self.file_url("nope.pdf"))
        self.assertEqual(resp.status_code, 404)

    def test_directory_path_returns_404(self):
        (self.root / "sub").mkdir()
        resp = self.client.get(self.file_url("sub"))
        self.assertEqual(resp.status_code, 404)

    def test_image_served_inline(self):
        self.write("圖.png", b"fakepng")
        resp = self.client.get(self.file_url("圖.png"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Disposition"].startswith("inline"))

    def test_disallowed_extension_returns_404(self):
        self.write("desktop.ini", b"junk")
        resp = self.client.get(self.file_url("desktop.ini"))
        self.assertEqual(resp.status_code, 404)


class BrowseTests(MaterialsTestBase):
    def test_root_lists_dirs_and_files_and_hides_dotfiles(self):
        self.write("a.pdf")
        self.write("photo.png")
        (self.root / "演算法").mkdir()
        self.write(".secret")
        resp = self.client.get("/materials/")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("a.pdf", body)
        self.assertIn("photo.png", body)
        self.assertIn("演算法", body)
        self.assertNotIn(".secret", body)

    def test_disallowed_extensions_are_filtered(self):
        self.write("good.pdf")
        self.write("desktop.ini")
        self.write("note.txt")
        self.write("script.exe")
        resp = self.client.get("/materials/")
        body = resp.content.decode()
        self.assertIn("good.pdf", body)
        self.assertIn("note.txt", body)
        self.assertNotIn("desktop.ini", body)
        self.assertNotIn("script.exe", body)
        names = [f["name"] for f in resp.context["files"]]
        self.assertEqual(names, ["good.pdf", "note.txt"])

    def test_subdir_listing_and_breadcrumb(self):
        self.write("演算法/第一章/講義.pdf")
        resp = self.client.get("/materials/", {"path": "演算法/第一章"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["current"], "演算法/第一章")
        crumb_names = [c["name"] for c in resp.context["crumbs"]]
        self.assertEqual(crumb_names, ["演算法", "第一章"])
        self.assertEqual([f["name"] for f in resp.context["files"]], ["講義.pdf"])

    def test_browse_path_traversal_returns_404(self):
        resp = self.client.get("/materials/", {"path": "../"})
        self.assertEqual(resp.status_code, 404)

    def test_browse_nonexistent_dir_returns_404(self):
        resp = self.client.get("/materials/", {"path": "nope"})
        self.assertEqual(resp.status_code, 404)
