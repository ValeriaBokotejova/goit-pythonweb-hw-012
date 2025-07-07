from typing import Optional

from pydantic import BaseModel, EmailStr

from app.roles import UserRole


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    is_verified: bool
    role: UserRole


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str | None = None
    is_verified: bool
    role: UserRole

    class Config:
        from_attributes = True


class AvatarUpdate(BaseModel):
    avatar_url: str
