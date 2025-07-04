from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=30)
    birthday: Optional[date] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    birthday: Optional[date] = None


class ContactRead(ContactBase):
    id: int

    class Config:
        from_attributes = True
