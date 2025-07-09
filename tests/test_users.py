import uuid

import pytest
from sqlalchemy import select

from app.db.session import async_session
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.auth import register_user


@pytest.mark.asyncio
async def test_create_user():
    uid = uuid.uuid4().hex[:6]
    user_data = {
        "username": f"user_{uid}",
        "email": f"user_{uid}@test.com",
        "password": "Password123",
    }

    async with async_session() as db1:
        resp = await register_user(UserCreate(**user_data), db1)
        assert "access_token" in resp

    async with async_session() as db2:
        saved = await db2.scalar(select(User).filter_by(email=user_data["email"]))
        assert saved.username == user_data["username"]
