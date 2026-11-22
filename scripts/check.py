"""Run what CI runs, locally: python scripts/check.py [--frontend]

Always: ruff, mypy and pytest. With --frontend: Biome, tsc and Vitest too. No network, no AI calls.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(name: str, command: list[str], cwd: Path = ROOT) -> bool:
    print(f"== {name}", flush=True)
    ok = subprocess.run(command, cwd=cwd, check=False).returncode == 0
    print(f"   {'ok' if ok else 'FAILED'}", flush=True)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--frontend", action="store_true", help="also lint, type check and test the frontend")
    args = parser.parse_args()

    python = sys.executable
    results = [
        run("ruff", [python, "-m", "ruff", "check", "."]),
        run("mypy", [python, "-m", "mypy"]),
        run("pytest", [python, "-m", "pytest", "-q"]),
    ]
    if args.frontend:
        npm = shutil.which("npm") or "npm"
        frontend = ROOT / "frontend"
        results += [run(f"frontend {name}", [npm, "run", name], frontend) for name in ("lint", "typecheck", "test")]

    print("\nAll checks passed." if all(results) else "\nSome checks FAILED.")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
