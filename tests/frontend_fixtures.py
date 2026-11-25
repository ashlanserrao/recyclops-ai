"""Real API responses saved for the browser tests (frontend/e2e/fixtures), checked against the API on every run.

The e2e tests stub the API with these files, so a backend change that alters a response fails here first.
After an intended change: UPDATE_FIXTURES=1 pytest, then review the diff.
"""

import json
import os
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parents[1] / "frontend" / "e2e" / "fixtures"


def assert_matches_fixture(name: str, data: Any) -> None:
    path = FIXTURES / name
    if os.environ.get("UPDATE_FIXTURES"):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    assert json.loads(path.read_text(encoding="utf-8")) == data, f"{name} is out of date (UPDATE_FIXTURES=1)"
