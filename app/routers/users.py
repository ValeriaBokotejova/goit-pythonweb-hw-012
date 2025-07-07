from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.models.user import User
from app.roles import UserRole
from app.schemas.user import AvatarUpdate, UserRead
from app.services.avatar import upload_avatar_to_cloudinary
from app.services.oauth2 import get_current_user
from app.services.rate_limit import rate_limiter
from app.services.users import update_avatar

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limiter)],
)
async def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch(
    "/avatar",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
async def update_avatar_from_data(
    avatar_data: AvatarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.avatar is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update the avatar more than once",
        )

    return await update_avatar(avatar_data, db, current_user)


@router.post(
    "/avatar",
    status_code=status.HTTP_200_OK,
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = await upload_avatar_to_cloudinary(
        file,
        public_id=f"user_avatars/{current_user.id}",
    )
    current_user.avatar = url
    db.add(current_user)
    await db.commit()
    return {"avatar_url": url}
