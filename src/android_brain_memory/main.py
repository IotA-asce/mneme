from __future__ import annotations

from pathlib import Path

from .storage import MemoryStore


def open_default_store() -> MemoryStore:
    return MemoryStore(Path(".local/android_brain_memory.sqlite3"))
