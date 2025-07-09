import pytest

from app.models.user import User
from app.services.admin import is_admin_email


@pytest.mark.asyncio
async def test_is_admin_email():
    user = User(email="admin@example.com", role="admin")
    assert is_admin_email(user) is True

    user = User(email="user@example.com", role="user")
    assert is_admin_email(user) is False
