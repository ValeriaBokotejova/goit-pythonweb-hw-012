import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.deps import get_db
from app.models.user import User
from app.schemas.auth import (
    EmailRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
)
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    hash_password,
    register_user,
    verify_email_token,
    verify_password,
)
from app.services.oauth2 import get_current_user
from app.utils.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


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


@router.post("/auth/password-reset-request")
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Password reset requested for non-existent email: {data.email}")
        raise HTTPException(status_code=404, detail="User not found")

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    reset_token = jwt.encode(
        token_data,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    send_password_reset_email(user.email, reset_token)

    logger.info(f"Password reset link sent to: {data.email}")
    return {"message": "Password reset link sent"}


@router.post("/auth/password-reset")
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        payload = jwt.decode(
            data.token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        email_from_token = payload.get("email")
        logger.info(f"Decoded token: email={email_from_token}")
    except JWTError as e:
        logger.error(f" Invalid token: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if email_from_token != data.email:
        raise HTTPException(status_code=400, detail="Email does not match token")

    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"Password reset failed: user not found ({data.email})")
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(data.new_password)
    await db.commit()

    logger.info(f"Password reset successful for user: {user.email}")
    return {"message": "Password changed successfully"}


@router.get("/reset-password", response_class=HTMLResponse)
async def show_reset_password_info(token: str):
    return HTMLResponse(
        content=f"""
        <h2>Password Reset Link</h2>
        <p>This is a backend-only app. To reset your password, send a POST request to:</p>
        <pre>/api/auth/password-reset</pre>
        <p>Include this token in your request:</p>
        <code>{token}</code>
        """,
        status_code=200,
    )
