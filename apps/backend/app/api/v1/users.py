"""
User management API endpoints (Admin only).
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, status, Query

from app.core.dependencies import DBSession, AdminUser
from app.core.exceptions import NotFoundException, ConflictException
from app.models.user import User, UserRole
from app.schemas.user import (
    UserResponse,
    UserUpdateByAdmin,
    UserCreate,
)
from app.schemas.common import PaginatedResponse, Message

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    db: DBSession,
    current_user: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
):
    """List all users (Admin only)."""
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: DBSession,
    current_user: AdminUser,
):
    """Create a new user (Admin only)."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise ConflictException("Email already registered")

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
    )
    user.set_password(user_data.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """Get user by ID (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundException("User not found")

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdateByAdmin,
    db: DBSession,
    current_user: AdminUser,
):
    """Update a user (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundException("User not found")

    # Prevent admin from deactivating themselves
    if user_id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    # Check email uniqueness if changing
    if user_data.email and user_data.email != user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise ConflictException("Email already in use")
        user.email = user_data.email

    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.bio is not None:
        user.bio = user_data.bio
    if user_data.avatar_url is not None:
        user.avatar_url = user_data.avatar_url
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_verified is not None:
        user.is_verified = user_data.is_verified

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """Delete a user (Admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundException("User not found")

    db.delete(user)
    db.commit()

    return Message(message="User deleted successfully")


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """Activate a user account (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundException("User not found")

    user.is_active = True
    db.commit()
    db.refresh(user)

    return user


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """Deactivate a user account (Admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundException("User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)

    return user


@router.post("/{user_id}/verify", response_model=UserResponse)
async def verify_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """Mark a user as verified (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundException("User not found")

    user.is_verified = True
    db.commit()
    db.refresh(user)

    return user
