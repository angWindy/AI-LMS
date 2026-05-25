"""
Authentication API endpoints.
"""
from datetime import datetime, timezone
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, DBSession, CurrentUser
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserUpdate, PasswordChange
from app.schemas.common import TokenResponse, Message, RefreshTokenRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


def _mask_password(value: str) -> str:
    """Mask password for safe operational logs."""
    if not value:
        return "<empty>"
    if len(value) <= 2:
        return "*" * len(value)
    return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: DBSession,
):
    # Đăng ký tài khoản mới.
    """Register a new user."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
    )
    new_user.set_password(user_data.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        "[Success] Register succeeded role=%s account=%s",
        new_user.role,
        new_user.email,
    )

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: DBSession,
):
    # Đăng nhập và phát hành access/refresh token.
    """Login and get access and refresh tokens."""
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token_value = create_refresh_token(user.id)

    # Store refresh token in database
    refresh_token = RefreshToken(user_id=user.id, token=refresh_token_value)
    db.add(refresh_token)
    db.commit()

    logger.info(
        "[Success] Login succeeded role=%s account=%s password_masked=%s",
        user.role,
        user.email,
        _mask_password(credentials.password),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: DBSession,
):
    # Cấp mới access token bằng refresh token.
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    # Verify refresh token exists in database
    refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.token == request.refresh_token,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Create new tokens
    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    # Revoke old refresh token
    refresh_token.revoked_at = datetime.now(timezone.utc)

    # Store new refresh token
    new_token_record = RefreshToken(user_id=user_id, token=new_refresh_token)
    db.add(new_token_record)
    db.commit()

    refreshed_user = db.query(User).filter(User.id == user_id).first()
    if refreshed_user:
        logger.info(
            "[Success] Token refresh succeeded role=%s account=%s",
            refreshed_user.role,
            refreshed_user.email,
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=Message)
async def logout(
    current_user: CurrentUser,
    db: DBSession,
):
    # Đăng xuất và thu hồi refresh token.
    """Logout and revoke all refresh tokens."""
    # Revoke all user's refresh tokens
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()

    logger.info(
        "[Success] Logout succeeded role=%s account=%s",
        current_user.role,
        current_user.email,
    )

    return Message(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser):
    # Lấy thông tin hồ sơ người dùng hiện tại.
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    # Cập nhật hồ sơ cá nhân.
    """Update current user profile."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.bio is not None:
        current_user.bio = user_update.bio

    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url

    db.commit()
    db.refresh(current_user)

    logger.info(
        "[Success] Profile update succeeded role=%s account=%s",
        current_user.role,
        current_user.email,
    )

    return current_user


@router.put("/me/password", response_model=Message)
async def change_password(
    password_data: PasswordChange,
    current_user: CurrentUser,
    db: DBSession,
):
    # Đổi mật khẩu cho tài khoản hiện tại.
    """Change current user password."""
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.set_password(password_data.new_password)
    db.commit()

    logger.info(
        "[Success] Password change succeeded role=%s account=%s old_password_masked=%s new_password_masked=%s",
        current_user.role,
        current_user.email,
        _mask_password(password_data.current_password),
        _mask_password(password_data.new_password),
    )

    return Message(message="Password changed successfully")
