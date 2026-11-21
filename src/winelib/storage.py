"""Small file helpers: tolerant reads, atomic writes."""

from __future__ import annotations

import os


def read_bytes(path: str) -> bytes | None:
    """Return the file content, or None when it is missing or unreadable."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def read_json(path: str):
    """Return parsed JSON, or None when the file is missing, empty or corrupt."""
    data = read_bytes(path)
    if not data:
        return None
    import json  # lazy, like everywhere on the search path

    try:
        return json.loads(data)
    except ValueError:
        return None


def write_file(path: str, data: bytes) -> None:
    """Write atomically so Alfred never reads a half-written file."""
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    tmp = os.path.join(folder, ".%s.%s.tmp" % (os.path.basename(path), os.urandom(4).hex()))
    try:
        with open(tmp, "xb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_json(path: str, data, indent: int | None = None) -> None:
    import json

    write_file(path, json.dumps(data, ensure_ascii=False, indent=indent).encode())
