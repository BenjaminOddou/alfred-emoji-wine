"""Small JSON helpers: tolerant reads, atomic writes."""

import json
import os
import tempfile
from typing import Any, Optional


def read_json(path: str) -> Optional[Any]:
    """Return parsed JSON, or None when the file is missing, empty or corrupt."""
    try:
        if os.path.getsize(path) == 0:
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def write_json(path: str, data: Any, indent: Optional[int] = None) -> None:
    """Write JSON atomically so Alfred never reads a half-written file."""
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=indent)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
