from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, MessageResponse, RegisterRequest, UserResponse
from app.services.auth_throttle import (
    assert_login_allowed,
    clear_login_failures,
    record_failed_login,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        if await self.users.get_by_email(payload.email.lower()):
            raise AppException("Email already registered", status_code=400)
        if await self.users.get_by_username(payload.username.lower()):
            raise AppException("Username already taken", status_code=400)

        user = User(
            email=payload.email.lower(),
            username=payload.username.lower(),
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=UserRole.STUDENT,
            is_active=True,
        )
        user = await self.users.create(user)
        token = create_access_token(str(user.id), {"role": user.role.value})
        return AuthResponse(user=UserResponse.model_validate(user), access_token=token)

    async def login(self, payload: LoginRequest) -> AuthResponse:
        email = payload.email.lower()
        await assert_login_allowed(email)
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(payload.password, user.password_hash):
            await record_failed_login(email)
            raise AppException("Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppException("Account is inactive", status_code=403)

        await clear_login_failures(email)
        token = create_access_token(str(user.id), {"role": user.role.value})
        return AuthResponse(user=UserResponse.model_validate(user), access_token=token)

    async def me(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def logout(self) -> MessageResponse:
        return MessageResponse(message="Logged out successfully")
