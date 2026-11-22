"""FastAPI app: the API routes plus (locally) the built frontend, wired together here.

Run with: uvicorn recyclops.api.main:app
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from recyclops.api.errors import add_error_handlers
from recyclops.api.middleware import guard_requests
from recyclops.api.routes import ask, health, plan
from recyclops.api.static import FrontendFiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# The React build (cd frontend && npm run build). The API works without it: in tests, and on Render,
# where Vercel serves the site. Found from this file's place in the repo, so it needs the editable install.
FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend" / "dist"

app = FastAPI(title="recyclops-ai", docs_url=None, redoc_url=None, openapi_url=None)
app.middleware("http")(guard_requests)
# Added last so it wraps the guard: every response leaves compressed with the guard's headers kept.
app.add_middleware(GZipMiddleware, minimum_size=1000)
add_error_handlers(app)
for routes in (health, plan, ask):
    app.include_router(routes.router)

# Mounted last: "/" would otherwise catch the API's paths too.
if FRONTEND_DIR.is_dir():
    app.mount("/", FrontendFiles(directory=FRONTEND_DIR, html=True), name="frontend")
