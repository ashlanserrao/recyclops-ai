"""The request guard and error format: what every route gets for free."""

import httpx
import pytest
from fastapi.testclient import TestClient

from recyclops.api.limits import RATE_LIMITERS
from recyclops.api.main import app
from recyclops.api.security import SECURITY_HEADERS
from recyclops.core.config import settings


def test_health_has_security_headers(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value
    assert "strict-transport-security" not in response.headers  # plain HTTP


def test_hsts_only_over_https() -> None:
    response = TestClient(app, base_url="https://testserver").get("/api/health")
    assert response.headers["strict-transport-security"] == "max-age=31536000"


def test_oversized_body_is_rejected(client: TestClient) -> None:
    response = client.post("/api/plan", content=b"x" * (settings.max_body_bytes + 1))
    assert response.status_code == 413
    assert response.json() == {"error": "Request is too large."}


def test_rate_limit_per_ip(client: TestClient) -> None:
    limit = RATE_LIMITERS["/api/air"].limit
    statuses = [client.get("/api/air").status_code for _ in range(limit + 1)]
    assert 429 not in statuses[:limit]
    assert statuses[-1] == 429


def test_unknown_route_gives_clean_json(client: TestClient) -> None:
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.json() == {"error": "Not found."}


def test_real_network_is_blocked() -> None:
    with pytest.raises(RuntimeError, match="network access is blocked"):
        httpx.get("https://example.com", timeout=1)
