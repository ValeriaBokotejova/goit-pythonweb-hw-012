"""
Authentication & authorisation helpers:
– password hashing / verifying
– JWT access & e-mail-verification tokens
– current-user dependency for routes
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.deps import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin
from app.utils.email import send_verification_email

# ──────────────────────────── constants ─────────────────────────── #

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
VERIFY_TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ──────────────────────────── helpers ───────────────────────────── #


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_verification_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=VERIFY_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:  # explicit chaining ✔️
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        ) from exc


# ───────────────────────── user-facing funcs ────────────────────── #


async def register_user(user_data: UserCreate, db: AsyncSession) -> dict:
    # uniqueness check
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

    # send verification e-mail
    token = create_verification_token(new_user.email)
    send_verification_email(new_user.email, token)

    return {
        "access_token": create_access_token({"sub": new_user.email}),
        "token_type": "bearer",
        "msg": "User created. Please check your email to verify your account.",
    }


async def verify_email_token(token: str, db: AsyncSession) -> dict:
    payload = decode_token(token)
    email = payload.get("sub")

    user = await db.scalar(select(User).filter_by(email=email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"msg": "Email already verified"}

    user.is_verified = True
    await db.commit()
    return {"msg": "Email successfully verified"}


async def authenticate_user(user_data: UserLogin, db: AsyncSession) -> dict:
    user = await db.scalar(select(User).filter_by(email=user_data.email))
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    return {
        "access_token": create_access_token({"sub": user.email}),
        "token_type": "bearer",
    }


# ───────────────────── FastAPI dependency ───────────────────────── #


# Universal dependency to extract token from either header or query
async def get_current_user(
    token: str | None = Query(
        default=None,
        description="JWT access token. Can be passed as query ?token=... or in headers as token: ...",
    ),
    token_header: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    jwt_token = token or token_header
    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
        )

    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.scalar(select(User).filter_by(email=email))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
