from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.deps import get_db
from app.models.user import User
from app.schemas.auth import EmailRequest, LoginRequest, TokenResponse, UserCreate
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    register_user,
    verify_email_token,
    verify_password,
)
from app.services.oauth2 import get_current_user
from app.utils.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user and send email verification link.
    """
    return await register_user(user_data, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return access + refresh token in response and as cookies.
    """
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

    access_token = create_access_token(
        {"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_refresh_token({"sub": user.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # change to True on production (HTTPS)
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(response: Response, user: User = Depends(get_current_user)):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"msg": f"User {user.email} successfully logged out"}


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify user email via token from email link.
    """
    try:
        await verify_email_token(token, db)
        return HTMLResponse(
            content="<h2>✅ Email verified successfully!</h2>",
            status_code=200,
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h2>❌ Verification failed:</h2><p>{str(e)}</p>",
            status_code=400,
        )


@router.post("/resend-verification")
async def resend_verification(
    request: EmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend verification email to unverified user.
    """
    user = await db.scalar(select(User).filter_by(email=request.email))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    token = create_verification_token(user.email)
    send_verification_email(user.email, token)

    return {"msg": "Verification email resent"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        new_access_token = create_access_token({"sub": email})

        response = JSONResponse(
            content={
                "access_token": new_access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            },
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.access_token_expire_minutes * 60,
        )
        return response

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
