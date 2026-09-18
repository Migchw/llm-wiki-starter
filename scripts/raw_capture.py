"""Store immutable capture bytes without replacing an existing file."""

import hashlib
import os
from pathlib import Path
import tempfile


def write_capture(output_dir: Path, stem: str, source: str, data: bytes,
                  suffix: str = ".md") -> Path:
    """Reuse an identical capture, or publish new bytes under a distinct name.

    Identity includes both the source and the complete stored bytes. Changes
    to metadata (including the capture date) therefore create a new snapshot.
    A temporary file and a no-replace hard link keep concurrent readers from
    seeing partially written captures. Existing names, including symlinks,
    are never overwritten.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_id = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    content_id = hashlib.sha256(data).hexdigest()[:16]
    destination = output_dir / f"{stem}_{source_id}_{content_id}{suffix}"

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix=".capture-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != data:
                raise FileExistsError(f"Refusing to replace existing capture: {destination}")
        return destination
    finally:
        if temporary is not None:
            temporary.unlink()
