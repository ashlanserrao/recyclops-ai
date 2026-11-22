import socket
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from recyclops.api import dependencies
from recyclops.api.limits import RATE_LIMITERS
from recyclops.api.main import app


class NetworkBlockedError(RuntimeError):
    """A test tried to open a real network connection."""


LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _host(address: Any) -> str:
    return str(address[0]) if isinstance(address, tuple) else str(address)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests never reach a real AQI source or AI provider, even with keys in .env.

    Blocked at the socket level, so it covers every client library. Loopback stays open: asyncio's
    event loop on Windows talks to itself through a local socket pair. TestClient and respx run
    in-process, so they still work.
    """
    def guarded(real: Any, host_of: Any) -> Any:
        def call(*args: Any, **kwargs: Any) -> Any:
            if host_of(*args) not in LOOPBACK:
                raise NetworkBlockedError("Real network access is blocked in tests: fake it with respx.")
            return real(*args, **kwargs)
        return call

    monkeypatch.setattr(socket.socket, "connect", guarded(socket.socket.connect, lambda _s, a, *__: _host(a)))
    monkeypatch.setattr(socket.socket, "connect_ex", guarded(socket.socket.connect_ex, lambda _s, a, *__: _host(a)))
    monkeypatch.setattr(socket, "create_connection", guarded(socket.create_connection, lambda a, *__: _host(a)))
    monkeypatch.setattr(socket, "getaddrinfo", guarded(socket.getaddrinfo, lambda h, *__: str(h)))


@pytest.fixture(autouse=True)
def no_real_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    """The app's AI chain has no providers in tests, even with keys in .env: templates answer."""
    monkeypatch.setattr(dependencies.ai, "providers", [])
    dependencies.ai._cache.clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    for limiter in RATE_LIMITERS.values():
        limiter.reset()
    yield TestClient(app)
    app.dependency_overrides.clear()
