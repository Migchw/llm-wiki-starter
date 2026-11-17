"""Local printed-text OCR for PDFs and large raster images."""

from contextlib import closing
from functools import lru_cache
from pathlib import Path
import sys

MODEL = "iapp/OpenThai2.0-OCR-Text"
REVISION = "40e8e9ff752b65153b1a71d521ec9390882afd7e"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
INSTALL = "Install OCR support with: python -m pip install -r scripts/requirements-ocr.txt"
MAX_EDGE = 3500


def needs_ocr(path: Path) -> bool:
    if path.suffix.lower() == ".pdf":
        return True
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return False
    if path.stat().st_size >= 2 * 1024**2:
        return True
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError(INSTALL) from error
    with Image.open(path) as image:
        return image.width * image.height >= 2_000_000 or getattr(image, "n_frames", 1) > 1


@lru_cache(maxsize=1)
def _engine():
    from huggingface_hub import snapshot_download

    # Load the matching runtime and ONNX weights from one immutable revision.
    directory = snapshot_download(
        MODEL, revision=REVISION,
        allow_patterns=["runtime/*.py", "det.onnx", "det.yml", "rec.onnx", "rec_dict.txt", "config.json"],
    )
    sys.path.insert(0, directory)
    try:
        from runtime.line_engine import LineOCR
    finally:
        sys.path.remove(directory)
    return LineOCR(directory, threads=1)


def _read_pages(path):
    if path.suffix.lower() == ".pdf":
        import pypdfium2 as pdfium

        with pdfium.PdfDocument(path) as document:
            for index in range(len(document)):
                with closing(document[index]) as page:
                    scale = min(200 / 72, MAX_EDGE / max(page.get_size()))
                    with closing(page.render(scale=scale)) as bitmap:
                        yield _engine().read(bitmap.to_pil())["text"].strip()
        return

    from PIL import Image, ImageOps, ImageSequence

    with Image.open(path) as source:
        source.draft("RGB", (MAX_EDGE, MAX_EDGE))
        for frame in ImageSequence.Iterator(source):
            # Work on a copy so resizing cannot affect subsequent TIFF frames.
            frame = ImageOps.exif_transpose(frame)
            frame.thumbnail((MAX_EDGE, MAX_EDGE))
            if frame.has_transparency_data:
                rgba = frame.convert("RGBA")
                frame = Image.new("RGB", rgba.size, "white")
                frame.paste(rgba, mask=rgba.getchannel("A"))
            yield _engine().read(frame)["text"].strip()


def ocr_markdown(path: Path) -> str:
    try:
        pages = list(_read_pages(path))
    except ImportError as error:
        raise RuntimeError(INSTALL) from error
    if not any(pages):
        raise ValueError(f"OpenThai OCR found no readable text in {path.name}")
    sections = []
    for index, text in enumerate(pages, 1):
        body = "  \n".join(text.splitlines()) if text else "*No text detected by OCR.*"
        sections.append(f"## Page {index}\n\n{body}")
    return "\n\n".join(sections)
