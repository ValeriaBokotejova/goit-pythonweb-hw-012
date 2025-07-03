from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    is_verified: bool
    role: str

    class Config:
        from_attributes = True


class AvatarUpdate(BaseModel):
    avatar_url: str
