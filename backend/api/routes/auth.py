"""api/routes/auth.py — Authentication endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.dependencies import get_db, get_current_user
from core.exceptions import UnauthorizedError, ValidationError
from database.models.models import User, RefreshToken, Portfolio
from database.repositories.user_repository import UserRepository
from auth.jwt_handler import (
    hash_password, verify_password, create_access_token,
    generate_refresh_token, hash_refresh_token, get_refresh_token_expiry,
)
from schemas.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, RefreshTokenRequest, UserResponse
from config import settings
from core.logging import logger

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.email_exists(payload.email):
        raise ValidationError("Email already registered")
    if await repo.username_exists(payload.username):
        raise ValidationError("Username already taken")
    user = await repo.create(
        email=payload.email.lower(),
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        risk_tolerance=payload.risk_tolerance or "moderate",
    )
    db.add(Portfolio(user_id=user.id, name="My Portfolio", is_default=True))
    await db.flush()
    logger.info("User registered", user_id=user.id)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")
    access_token = create_access_token(user.id)
    raw_refresh, hashed_refresh = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hashed_refresh, expires_at=get_refresh_token_expiry()))
    logger.info("User logged in", user_id=user.id)
    return {
        "access_token": access_token, "refresh_token": raw_refresh,
        "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(
        RefreshToken.token_hash == token_hash, RefreshToken.is_revoked == False
    ))
    stored = result.scalar_one_or_none()
    if not stored or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise UnauthorizedError("Invalid or expired refresh token")
    stored.is_revoked = True
    raw_refresh, hashed_refresh = generate_refresh_token()
    db.add(RefreshToken(user_id=stored.user_id, token_hash=hashed_refresh, expires_at=get_refresh_token_expiry()))
    return {
        "access_token": create_access_token(stored.user_id), "refresh_token": raw_refresh,
        "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    await db.execute(update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(is_revoked=True))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
