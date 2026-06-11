from pathlib import Path

from android_brain_memory.storage import MemoryStore

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / ".local" / "android_brain_memory.sqlite3"
MIGRATION = ROOT / "storage" / "migrations" / "001_init.sql"

store = MemoryStore(DB)
store.apply_migration(MIGRATION)
store.close()
print(f"Initialized database at {DB}")
