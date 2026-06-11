from pathlib import Path

from android_brain_memory.storage import MemoryStore

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / ".local" / "android_brain_memory.sqlite3"
MIGRATIONS = ROOT / "storage" / "migrations"

store = MemoryStore(DB)
applied = store.run_migrations(MIGRATIONS)
store.close()
if applied:
    applied_ids = ", ".join(record.migration_id for record in applied)
    print(f"Initialized database at {DB}; applied migrations: {applied_ids}")
else:
    print(f"Initialized database at {DB}; migrations already up to date")
