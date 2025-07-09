import uuid

import pytest
from sqlalchemy import select

from app.models.contact import Contact
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.contact import ContactCreate
from app.services.auth import register_user, verify_email_token
from app.services.contacts import create_contact


@pytest.mark.asyncio
async def test_create_contact(db):
    uid = uuid.uuid4().hex[:6]
    user_data = {
        "username": f"user_{uid}",
        "email": f"user_{uid}@test.com",
        "password": "SecurePass123",
    }
    signup = await register_user(UserCreate(**user_data), db)
    token = signup["access_token"]
    await verify_email_token(token, db)
    user: User = await db.scalar(select(User).filter_by(email=user_data["email"]))

    phone = f"+1-555-{uuid.uuid4().hex[:4]}"
    contact_in = ContactCreate(
        first_name="Alice",
        last_name="Smith",
        email=f"alice_{uid}@test.com",
        phone=phone,
    )
    contact: Contact = await create_contact(contact_in, db, user)
    assert contact.email == contact_in.email

    saved = await db.scalar(select(Contact).filter_by(email=contact_in.email))
    assert saved.first_name == "Alice"
