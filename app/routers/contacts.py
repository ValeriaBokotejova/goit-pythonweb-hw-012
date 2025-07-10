"""
Contacts API endpoints.

This module defines all CRUD and search endpoints for managing contacts.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services.contacts import (
    create_contact,
    delete_contact,
    get_contact_by_id,
    get_contacts,
    get_upcoming_birthdays,
    search_contacts,
    update_contact,
)
from app.services.oauth2 import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post(
    "/",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact_view(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactRead:
    """
    Create a new contact for the current user.

    - **contact**: Contact payload (first name, last name, email, phone, birthday).
    - **db**: Async database session.
    - **current_user**: Authenticated user object.

    Returns the created Contact.
    """
    return await create_contact(contact, db, current_user)


@router.get(
    "/",
    response_model=List[ContactRead],
)
async def list_contacts(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ContactRead]:
    """
    Retrieve a paginated list of contacts for the current user.

    - **skip**: Number of records to skip.
    - **limit**: Maximum number of records to return.
    """
    return await get_contacts(skip, limit, db, current_user)


@router.get(
    "/search",
    response_model=List[ContactRead],
)
async def search_contacts_view(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ContactRead]:
    """
    Search contacts by first name, last name or email for the current user.

    - **query**: Substring to search.
    """
    return await search_contacts(query, db, current_user)


@router.get(
    "/upcoming/birthdays",
    response_model=List[ContactRead],
)
async def upcoming_birthdays_view(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ContactRead]:
    """
    Retrieve contacts whose birthdays occur within the next 7 days.
    """
    return await get_upcoming_birthdays(db, current_user)


@router.get(
    "/{contact_id}",
    response_model=ContactRead,
)
async def get_contact_view(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactRead:
    """
    Get a single contact by its ID for the current user.

    - **contact_id**: ID of the contact to retrieve.
    """
    return await get_contact_by_id(contact_id, db, current_user)


@router.put(
    "/{contact_id}",
    response_model=ContactRead,
)
async def update_contact_view(
    contact_id: int,
    contact_data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactRead:
    """
    Update an existing contact.

    - **contact_id**: ID of the contact to update.
    - **contact_data**: Fields to change (any subset of first name, last name, email, phone, birthday).
    """
    return await update_contact(contact_id, contact_data, db, current_user)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_contact_view(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a contact by its ID.

    - **contact_id**: ID of the contact to delete.
    """
    await delete_contact(contact_id, db, current_user)
