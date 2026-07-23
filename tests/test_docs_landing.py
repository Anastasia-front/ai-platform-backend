import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_platform_test",
)
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("STORAGE_PROVIDER", "local")

from fastapi.testclient import TestClient

from app.main import app
from app.web.docs_landing import GITHUB_REPOSITORY_URL


client = TestClient(app)


def test_docs_landing_returns_html_with_resource_links():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    assert "/swagger" in html
    assert "/redoc" in html
    assert "/openapi.json" in html
    assert "/health" in html
    assert "https://ai-automation-platform.com" in html
    assert GITHUB_REPOSITORY_URL in html


def test_swagger_ui_is_available_at_swagger():
    response = client.get("/swagger")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "swagger" in response.text.lower()


def test_redoc_is_available():
    response = client.get("/redoc")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "redoc" in response.text.lower()


def test_openapi_json_is_available_and_valid():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "AI Automation Platform"
    assert "paths" in schema


def test_legacy_docs_redirects_to_swagger():
    response = client.get("/docs", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/swagger"


def test_docs_landing_and_redirect_are_not_in_openapi_schema():
    response = client.get("/openapi.json")

    paths = response.json()["paths"]
    assert "/" not in paths
    assert "/docs" not in paths
