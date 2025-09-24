"""Utility functions."""

import mimetypes
from pathlib import Path


def infer_file_type(file_path: str | Path) -> str:
    """Infer MIME type from file path.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string (defaults to 'application/octet-stream' if unknown)
    """
    path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "application/octet-stream"


def read_file_data(file_path: str | Path) -> bytes:
    """Read file data from path.

    Args:
        file_path: Path to the file

    Returns:
        File binary data
    """
    path = Path(file_path)
    with path.open("rb") as f:
        return f.read()
