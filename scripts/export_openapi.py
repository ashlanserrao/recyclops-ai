"""Write the API's OpenAPI schema to frontend/openapi.json, for `npm run gen:types` (typed API client).

The app serves no schema or docs (openapi_url=None); app.openapi() builds one anyway.
Run from the repo root: .\\venv\\Scripts\\python.exe scripts\\export_openapi.py
"""

import json
from pathlib import Path

from recyclops.api.main import app

OUTPUT = Path(__file__).resolve().parents[1] / "frontend" / "openapi.json"


def main() -> None:
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
