import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import LoginRequest, UserCreate
from app.services.auth import register_user, verify_email_token


@pytest.mark.asyncio
async def test_signup_and_login(client, db):
    uid = uuid.uuid4().hex[:6]
    user_data = {
        "username": f"user_{uid}",
        "email": f"user_{uid}@test.com",
        "password": "TestPass123",
    }
    resp = await client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201

    token = resp.json()["access_token"]
    verify_resp = await verify_email_token(token, db)
    assert "msg" in verify_resp

    login_data = LoginRequest(
        **{"email": user_data["email"], "password": user_data["password"]},
    )
    resp = await client.post("/api/auth/login", json=login_data.dict())
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data
