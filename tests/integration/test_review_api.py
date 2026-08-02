"""Integration tests for the Review API."""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(async_client: AsyncClient):
    # Register
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"

    # Login
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    return token_data["access_token"]


@pytest.mark.asyncio
async def test_submit_snippet_review(async_client: AsyncClient):
    # Register + login first
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "reviewer@example.com", "password": "password123"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # Submit snippet review
    resp = await async_client.post(
        "/api/v1/reviews",
        json={
            "type": "SNIPPET",
            "snippet_content": "import os\npassword = 'secret123'\nos.system(f'rm -rf {password}')",
            "snippet_language": "python",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["type"] == "SNIPPET"
    assert data["status"] == "PENDING"
    assert "id" in data


@pytest.mark.asyncio
async def test_submit_review_without_auth_returns_401(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/reviews",
        json={"type": "SNIPPET", "snippet_content": "x = 1"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_reviews_empty(async_client: AsyncClient):
    # New user, empty history
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "empty@example.com", "password": "password123"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "empty@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await async_client.get(
        "/api/v1/reviews",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_snippet_review_requires_content(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "val@example.com", "password": "password123"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "val@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await async_client.post(
        "/api/v1/reviews",
        json={"type": "SNIPPET"},  # Missing snippet_content
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_frontend_is_served_by_api(async_client: AsyncClient):
    home = await async_client.get("/")
    assert home.status_code == 200
    assert "CodeGuardian" in home.text

    api_client = await async_client.get("/api.js")
    assert api_client.status_code == 200
    assert "window.CodeGuardian" in api_client.text


@pytest.mark.asyncio
async def test_upload_and_list_knowledge_document(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "knowledge@example.com", "password": "password123"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "knowledge@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ingest = AsyncMock()
    monkeypatch.setattr("app.routers.knowledge._ingest_document_bg", ingest)

    upload = await async_client.post(
        "/api/v1/knowledge/upload",
        headers=headers,
        data={"title": "Secure Coding", "category": "coding_standard", "version": "1.0"},
        files={"file": ("secure.md", b"# Secure coding", "text/markdown")},
    )
    assert upload.status_code == 202
    assert upload.json()["title"] == "Secure Coding"

    documents = await async_client.get("/api/v1/knowledge/documents", headers=headers)
    assert documents.status_code == 200
    assert len(documents.json()) == 1
    assert documents.json()[0]["file_type"] == "md"
