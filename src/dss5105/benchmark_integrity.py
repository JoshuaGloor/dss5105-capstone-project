"""Explicit source hashing modes shared by offline benchmark tooling and tests."""

import hashlib
from pathlib import Path


def hash_bytes(data: bytes, *, mode: str) -> str:
    """Normalize line endings only for explicitly declared UTF-8 text sources."""
    if mode == "normalized_text_sha256":
        data.decode("utf-8", errors="strict")
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    elif mode != "raw_bytes_sha256":
        raise ValueError(f"Unknown source hash mode: {mode}")
    return hashlib.sha256(data).hexdigest()


def source_sha256(path: Path, *, mode: str) -> str:
    """Read binary so Python's newline translation cannot alter raw-byte mode."""
    return hash_bytes(path.read_bytes(), mode=mode)
