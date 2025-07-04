from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactUpdate


async def get_contacts(
    skip: int,
    limit: int,
    db: AsyncSession,
    user: User,
) -> List[Contact]:
    stmt = select(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contact_by_id(contact_id: int, db: AsyncSession, user: User) -> Contact:
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user.id),
    )
    result = await db.execute(stmt)
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact


async def create_contact(
    contact_data: ContactCreate,
    db: AsyncSession,
    user: User,
) -> Contact:
    new_contact = Contact(**contact_data.dict(), user_id=user.id)
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact


async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: AsyncSession,
    user: User,
) -> Contact:
    contact = await get_contact_by_id(contact_id, db, user)
    for field, value in contact_data.dict(exclude_unset=True).items():
        setattr(contact, field, value)
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    contact = await get_contact_by_id(contact_id, db, user)
    await db.delete(contact)
    await db.commit()


async def get_upcoming_birthdays(db: AsyncSession, user: User) -> List[Contact]:
    today = date.today()
    next_week = today + timedelta(days=7)

    stmt = select(Contact).filter(Contact.user_id == user.id)
    result = await db.execute(stmt)
    all_contacts = result.scalars().all()

    upcoming_birthdays = [
        contact
        for contact in all_contacts
        if contact.birthday
        and today <= contact.birthday.replace(year=today.year) <= next_week
    ]

    return upcoming_birthdays
