from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthConfigResponse,
    AuthResponse,
    GoogleLoginRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_policy import REGISTRATION_CLOSED, registration_open
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config() -> AuthConfigResponse:
    return AuthConfigResponse(public_registration_enabled=registration_open())


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    if not registration_open():
        raise AppException(REGISTRATION_CLOSED, status_code=403)
    return await AuthService(db).register(payload)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await AuthService(db).login(payload)


@router.post("/google", response_model=AuthResponse)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await AuthService(db).login_with_google(payload.credential)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
async def logout(_current_user: User = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Logged out successfully")
