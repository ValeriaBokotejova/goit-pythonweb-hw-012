from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import AvatarUpdate


async def update_avatar(
    avatar_data: AvatarUpdate,
    db: AsyncSession,
    current_user: User,
) -> User:
    current_user.avatar = avatar_data.avatar_url
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
