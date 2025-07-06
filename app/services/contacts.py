from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactUpdate
from app.services.cache import (
    cache_birthdays,
    cache_contacts,
    cache_search_results,
    get_cached_birthdays,
    get_cached_contacts,
    get_cached_search_results,
    invalidate_contacts_cache,
)


async def get_contacts(
    skip: int,
    limit: int,
    db: AsyncSession,
    user: User,
) -> List[Contact]:
    cached = await get_cached_contacts(user.id)
    if cached:
        return [Contact(**c) for c in cached]

    stmt = select(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    contacts = result.scalars().all()

    serialized = [c.__dict__ for c in contacts]
    for item in serialized:
        item.pop("_sa_instance_state", None)
    await cache_contacts(user.id, serialized)

    return contacts


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

    await invalidate_contacts_cache(user.id)
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

    await invalidate_contacts_cache(user.id)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    contact = await get_contact_by_id(contact_id, db, user)
    await db.delete(contact)
    await db.commit()

    await invalidate_contacts_cache(user.id)


async def get_upcoming_birthdays(db: AsyncSession, user: User) -> List[Contact]:
    cached = await get_cached_birthdays(user.id)
    if cached:
        return [Contact(**c) for c in cached]

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

    serialized = [c.__dict__ for c in upcoming_birthdays]
    for item in serialized:
        item.pop("_sa_instance_state", None)
    await cache_birthdays(user.id, serialized)

    return upcoming_birthdays


async def search_contacts(
    query: str,
    db: AsyncSession,
    user: User,
) -> List[Contact]:
    cached = await get_cached_search_results(user.id, query)
    if cached:
        return [Contact(**c) for c in cached]

    stmt = select(Contact).filter(
        Contact.user_id == user.id,
        or_(
            Contact.first_name.ilike(f"%{query}%"),
            Contact.last_name.ilike(f"%{query}%"),
            Contact.email.ilike(f"%{query}%"),
        ),
    )
    result = await db.execute(stmt)
    contacts = result.scalars().all()

    serialized = [c.__dict__ for c in contacts]
    for item in serialized:
        item.pop("_sa_instance_state", None)
    await cache_search_results(user.id, query, serialized)

    return contacts
