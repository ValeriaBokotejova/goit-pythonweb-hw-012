from __future__ import annotations

import logging

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.tokens import create_access_token, create_refresh_token, verify_token
from app.utils.email import send_verification_email

tmp_logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
VERIFY_TOKEN_EXPIRE_HOURS = settings.verify_token_expire_hours


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_verification_token(email: str) -> str:
    from datetime import datetime, timedelta

    expire = datetime.utcnow() + timedelta(hours=VERIFY_TOKEN_EXPIRE_HOURS)
    return create_access_token({"sub": email, "exp": expire})


async def register_user(user_data: UserCreate, db: AsyncSession) -> dict:

    if await db.scalar(select(User).filter_by(email=user_data.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    if await db.scalar(select(User).filter_by(username=user_data.username)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username already exists",
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hash_password(user_data.password),
        is_verified=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_verification_token(new_user.email)
    try:
        send_verification_email(new_user.email, token)
    except Exception as e:
        tmp_logger.warning(f"Failed to send verification email: {e}")

    return {
        "access_token": create_access_token({"sub": new_user.email}),
        "refresh_token": create_refresh_token({"sub": new_user.email}),
        "token_type": "bearer",
        "msg": "User created. Please check your email to verify your account.",
    }


async def verify_email_token(token: str, db: AsyncSession) -> dict:
    payload = verify_token(token)
    email = payload.get("sub")

    user = await db.scalar(select(User).filter_by(email=email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"msg": "Email already verified"}

    user.is_verified = True
    await db.commit()
    return {"msg": "Email successfully verified"}
