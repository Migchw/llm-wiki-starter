"""Offline routing and Markdown tests. Model weights are not needed."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import openthai_ocr as ocr

try:
    from PIL import Image
except ImportError:
    Image = None


class OCRTests(unittest.TestCase):
    def test_routes_pdf_and_office_without_loading_model(self):
        self.assertTrue(ocr.needs_ocr(Path("scan.PDF")))
        self.assertFalse(ocr.needs_ocr(Path("slides.pptx")))

    @unittest.skipUnless(Image, "Pillow is needed for image routing tests")
    def test_image_size_and_multiple_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "scan.PNG"
            Image.new("L", (1999, 1000)).save(image)
            self.assertFalse(ocr.needs_ocr(image))
            Image.new("L", (2000, 1000)).save(image)
            self.assertTrue(ocr.needs_ocr(image))

            tiff = image.with_suffix(".tif")
            page = Image.new("L", (50, 50))
            page.save(tiff, save_all=True, append_images=[page])
            self.assertTrue(ocr.needs_ocr(tiff))

            bitmap = image.with_suffix(".bmp")
            Image.new("RGB", (1000, 1000)).save(bitmap)
            self.assertTrue(ocr.needs_ocr(bitmap))

    def test_pages_keep_order_line_breaks_and_empty_page_numbers(self):
        with patch.object(ocr, "_read_pages", return_value=["รายได้\n12345", "", "Final"]):
            self.assertEqual(
                ocr.ocr_markdown(Path("scan.pdf")),
                "## Page 1\n\nรายได้  \n12345\n\n## Page 2\n\n*No text detected by OCR.*\n\n## Page 3\n\nFinal",
            )

    def test_no_text_fails_before_capture(self):
        with patch.object(ocr, "_read_pages", return_value=["", ""]):
            with self.assertRaisesRegex(ValueError, "no readable text"):
                ocr.ocr_markdown(Path("empty.pdf"))
