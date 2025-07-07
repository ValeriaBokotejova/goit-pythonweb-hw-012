import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.roles import UserRole
from app.services.auth import hash_password

logger = logging.getLogger("admin")


async def create_admin(db: AsyncSession):
    admin_email = settings.admin_email
    admin_password = settings.admin_password

    if not admin_email or not admin_password:
        logger.error("❌ ADMIN_EMAIL or ADMIN_PASSWORD is not set in the environment.")
        return

    result = await db.execute(select(User).filter_by(email=admin_email))
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        logger.info(f"✅ Admin already exists: {admin_email}")
        return

    admin = User(
        username="admin",
        email=admin_email,
        password=hash_password(admin_password),
        is_verified=True,
        role=UserRole.ADMIN.value,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    logger.info(f"✅ Admin created successfully: {admin.email}")
