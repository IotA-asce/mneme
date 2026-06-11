from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def run_step(label: str, command: list[str]) -> None:
    print(f"\n==> {label}", flush=True)
    print("+ " + " ".join(command), flush=True)
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC) if not existing_pythonpath else f"{SRC}{os.pathsep}{existing_pythonpath}"
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> int:
    steps = [
        ("Initialize local SQLite database", [sys.executable, "scripts/init_db.py"]),
        ("Run memory smoke test", [sys.executable, "scripts/smoke_test_memory.py"]),
        ("Run pytest suite", [sys.executable, "-m", "pytest"]),
    ]
    for label, command in steps:
        run_step(label, command)
    print("\nDeveloper check completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
