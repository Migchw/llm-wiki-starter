"""Offline regression tests; run with python -m unittest discover -s tests -v."""

import concurrent.futures
import importlib.util
import io
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_fetcher(relative):
    spec = importlib.util.spec_from_file_location(relative, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    # Exercise storage without installing or contacting extraction providers.
    missing_providers = dict.fromkeys(
        ["bs4", "markitdown", "playwright.sync_api", "youtube_transcript_api"]
    )
    with patch.dict(sys.modules, missing_providers):
        with patch.object(sys, "path", [str(ROOT / "scripts")] + sys.path):
            spec.loader.exec_module(module)
    return module


FETCHERS = [
    load_fetcher("scripts/fetch_source.py"),
    load_fetcher(".agents/scripts/fetch_source.py"),
]


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def web(self, module, url, title, body="original evidence", output=None):
        with patch.object(module, "fetch_url_http", return_value="fixture"):
            with patch.object(module, "extract_content_from_html", return_value=(
                title, "Author", "Publisher", "2026-01-01", body
            )):
                return module.fetch_url(url, output_dir=output or self.root)

    def test_different_sources_with_colliding_titles_preserve_both(self):
        title_pairs = [
            ("รายงานบริษัทแรก", "รายงานบริษัทสอง"),
            ("Annual report", "Annual report"),
            ("a" * 60 + " first", "a" * 60 + " second"),
        ]
        for index, module in enumerate(FETCHERS):
            for pair_index, (first_title, second_title) in enumerate(title_pairs):
                with self.subTest(fetcher=module.__name__, titles=first_title):
                    output = self.root / str(index) / str(pair_index)
                    first = self.web(module, "https://example.test/first", first_title, output=output)
                    original = first.read_bytes()
                    second = self.web(module, "https://example.test/second", second_title, output=output)
                    self.assertNotEqual(first, second)
                    self.assertEqual(first.read_bytes(), original)
                    self.assertEqual(len(list(output.glob("*.md"))), 2)

    def test_unchanged_capture_reuses_file_and_changed_content_keeps_old_bytes(self):
        for index, module in enumerate(FETCHERS):
            with self.subTest(fetcher=module.__name__):
                output = self.root / str(index)
                first = self.web(module, "https://example.test/report", "Report", output=output)
                original, mtime = first.read_bytes(), first.stat().st_mtime_ns
                repeated = self.web(module, "https://example.test/report", "Report", output=output)
                changed = self.web(module, "https://example.test/report", "Report", "revised evidence", output)
                self.assertEqual(first, repeated)
                self.assertNotEqual(first, changed)
                self.assertEqual(first.read_bytes(), original)
                self.assertEqual(first.stat().st_mtime_ns, mtime)
                self.assertIn("revised evidence", changed.read_text())

    def test_legacy_markdown_is_never_replaced(self):
        legacy = self.root / "20260101_.md"
        legacy.write_bytes(b"existing raw evidence")
        for module in FETCHERS:
            with self.subTest(fetcher=module.__name__):
                new = self.web(module, "https://example.test/report", "รายงาน")
                self.assertNotEqual(new, legacy)
                self.assertEqual(legacy.read_bytes(), b"existing raw evidence")

    def test_videos_with_same_title_keep_separate_transcripts(self):
        metadata = b'"title":{"runs":[{"text":"Shared title"}]} "publishDate":"2026-01-01"'
        api = SimpleNamespace(
            list=lambda video_id: [],
            fetch=lambda video_id, **kwargs: SimpleNamespace(
                snippets=[SimpleNamespace(start=0, text="Transcript " + video_id)]
            ),
        )
        for index, module in enumerate(FETCHERS):
            with self.subTest(fetcher=module.__name__):
                with patch.object(module.urllib.request, "urlopen", side_effect=lambda *a, **k: io.BytesIO(metadata)):
                    with patch.object(module, "YouTubeTranscriptApi", return_value=api):
                        first = module.fetch_youtube_video("https://youtu.be/abcdefghijk", self.root / str(index))
                        original = first.read_bytes()
                        second = module.fetch_youtube_video("https://youtu.be/12345678901", self.root / str(index))
                self.assertNotEqual(first, second)
                self.assertEqual(first.read_bytes(), original)
                self.assertIn("abcdefghijk", first.read_text())
                self.assertIn("12345678901", second.read_text())

    def test_local_files_with_same_name_preserve_both_sources_and_captures(self):
        sources = []
        for name in ("first", "second"):
            source = self.root / name / "report.txt"
            source.parent.mkdir()
            source.write_text(name)
            sources.append(source)
        for index, module in enumerate(FETCHERS):
            with self.subTest(fetcher=module.__name__):
                with patch.object(module, "__file__", str(self.root / str(index) / "scripts" / "fetch_source.py")):
                    first = module.convert_local_file(str(sources[0]))
                    original = first.read_bytes()
                    second = module.convert_local_file(str(sources[1]))
                    sources[0].write_text("revised first")
                    revision = module.convert_local_file(str(sources[0]))
                    sources[0].write_text("first")
                self.assertNotEqual(first, second)
                self.assertNotEqual(first, revision)
                self.assertEqual(first.read_bytes(), original)
                self.assertEqual([p.read_text() for p in sources], ["first", "second"])

    def document(self, url, data, output):
        module = FETCHERS[0]
        converter = SimpleNamespace(convert=lambda path: SimpleNamespace(text_content="Document evidence"))
        with patch.object(module.urllib.request, "urlopen", return_value=io.BytesIO(data)):
            with patch.object(module, "MarkItDown", return_value=converter):
                note = module.fetch_document_url(url, output_dir=output)
        raw = Path(re.search(r'^raw_file: "(.*)"$', note.read_text(), re.M).group(1))
        return note, raw

    def test_document_staging_and_legacy_destinations_remain_unchanged(self):
        today = FETCHERS[0].datetime.date.today().strftime("%Y%m%d")
        legacy = [self.root / "report.pdf", self.root / (today + "_report.pdf"), self.root / (today + "_report.md")]
        for path in legacy:
            path.write_bytes(b"existing " + path.name.encode())
        before = {path: path.read_bytes() for path in legacy}
        note, raw = self.document("https://example.test/report.pdf", b"%PDF-new", self.root)
        self.assertEqual(raw.read_bytes(), b"%PDF-new")
        self.assertNotIn(note, legacy)
        self.assertNotIn(raw, legacy)
        self.assertEqual({path: path.read_bytes() for path in legacy}, before)

    def test_document_revisions_preserve_matching_binary_and_note(self):
        url = "https://example.test/report.pdf"
        note, raw = self.document(url, b"%PDF-first", self.root)
        original = {note: note.read_bytes(), raw: raw.read_bytes()}
        self.assertEqual(self.document(url, b"%PDF-first", self.root), (note, raw))
        second_note, second_raw = self.document(url, b"%PDF-second", self.root)
        other_note, other_raw = self.document("https://other.test/report.pdf", b"%PDF-first", self.root)
        self.assertEqual({path: path.read_bytes() for path in original}, original)
        self.assertEqual(len({note, second_note, other_note}), 3)
        self.assertEqual(len({raw, second_raw, other_raw}), 3)
        self.assertEqual(second_raw.read_bytes(), b"%PDF-second")

    def test_document_keeps_original_extension(self):
        for extension in (".pdf", ".docx", ".pptx", ".xlsx"):
            with self.subTest(extension=extension):
                _, raw = self.document("https://example.test/report" + extension, b"document bytes", self.root)
                self.assertEqual(raw.suffix, extension)
                self.assertEqual(raw.read_bytes(), b"document bytes")

    def test_concurrent_article_captures_do_not_overwrite(self):
        for index, module in enumerate(FETCHERS):
            with self.subTest(fetcher=module.__name__):
                output = self.root / str(index)
                with patch.object(module, "fetch_url_http", return_value="fixture"):
                    with patch.object(module, "extract_content_from_html", side_effect=lambda html, url: (
                        "Shared title", "Author", "Publisher", "2026-01-01", "evidence " + url
                    )):
                        urls = ["https://example.test/" + str(i % 4) for i in range(16)]
                        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                            paths = list(pool.map(lambda url: module.fetch_url(url, output_dir=output), urls))
                self.assertEqual(len(set(paths)), 4)
                for url, path in zip(urls, paths):
                    self.assertIn("evidence " + url, path.read_text())
                self.assertFalse(list(output.glob(".capture-*")))

    def test_conflicting_existing_file_is_not_overwritten(self):
        module = FETCHERS[0]
        destination = self.web(module, "https://example.test/report", "Report")
        destination.write_bytes(b"evidence modified outside the fetcher")
        with self.assertRaises(FileExistsError):
            self.web(module, "https://example.test/report", "Report")
        self.assertEqual(destination.read_bytes(), b"evidence modified outside the fetcher")
        self.assertFalse(list(self.root.glob(".capture-*")))

    def test_existing_symlink_is_never_followed_or_replaced(self):
        module = FETCHERS[0]
        destination = self.web(module, "https://example.test/report", "Report")
        destination.unlink()
        target = self.root / "unrelated-evidence.md"
        target.write_bytes(b"unrelated evidence")
        try:
            destination.symlink_to(target)
        except OSError as error:
            self.skipTest(f"Symlink creation is unavailable: {error}")
        for dangling in (False, True):
            with self.subTest(dangling=dangling):
                if dangling:
                    target.unlink()
                with self.assertRaises(FileExistsError):
                    self.web(module, "https://example.test/report", "Report")
                self.assertTrue(destination.is_symlink())
                if dangling:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), b"unrelated evidence")
        self.assertFalse(list(self.root.glob(".capture-*")))

    def test_publication_failure_cleans_only_owned_temporary_files(self):
        legacy = self.root / "existing.md"
        legacy.write_bytes(b"existing evidence")
        with patch("os.link", side_effect=OSError("publication failed")):
            with self.assertRaisesRegex(OSError, "publication failed"):
                self.web(FETCHERS[0], "https://example.test/report", "Report")
        self.assertEqual(list(self.root.iterdir()), [legacy])
        self.assertEqual(legacy.read_bytes(), b"existing evidence")


if __name__ == "__main__":
    unittest.main()
