from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.deps import get_db
from app.models.user import User
from app.schemas.auth import (
    EmailRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.services.auth import (
    authenticate_user,
    create_verification_token,
    register_user,
    verify_email_token,
)
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
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    """
    return await authenticate_user(user_data, db)


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
