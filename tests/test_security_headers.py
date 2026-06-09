from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.middleware.security_headers_middleware import SecurityHeadersMiddleware


def test_security_headers_are_added():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    response = TestClient(app).get("/ping")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "camera=(self)" in response.headers["Permissions-Policy"]
