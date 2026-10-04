import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.auth_identity import UserAuthIdentity
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_throttle import (
    assert_login_allowed,
    clear_login_failures,
    record_failed_login,
)
from app.services.google_identity import GoogleProfile, GoogleTokenError, verify_google_id_token

_USERNAME_BREAKS = re.compile(r"[^a-z0-9]+")
_GOOGLE = "google"


def username_base(email: str, full_name: str | None) -> str:
    local = email.split("@", 1)[0].lower()
    raw = _USERNAME_BREAKS.sub("", local)
    if len(raw) < 3 and full_name:
        raw = _USERNAME_BREAKS.sub("", full_name.lower())
    raw = raw[:80]
    if len(raw) < 3:
        raw = (raw + "student")[:12]
    return raw


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
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
        return self._auth_response(user, is_new_user=True)

    async def login(self, payload: LoginRequest) -> AuthResponse:
        email = payload.email.lower()
        await assert_login_allowed(email)
        user = await self.users.get_by_email(email)
        password_ok = bool(
            user
            and user.password_hash
            and verify_password(payload.password, user.password_hash)
        )
        if user is None or not password_ok:
            await record_failed_login(email)
            raise AppException("Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppException("Account is inactive", status_code=403)

        await clear_login_failures(email)
        return self._auth_response(user, is_new_user=False)

    async def login_with_google(self, credential: str) -> AuthResponse:
        client_id = settings.google_client_id.strip()
        if not client_id:
            raise AppException("Google sign-in is not configured", status_code=503)
        try:
            profile = verify_google_id_token(credential, client_id)
        except GoogleTokenError:
            raise AppException("Google sign-in failed", status_code=401) from None

        identity = await self._identity_by_subject(profile.subject)
        if identity is not None:
            user = await self.users.get_by_id(identity.user_id)
            if user is None or not user.is_active:
                raise AppException("Account is inactive", status_code=403)
            return self._auth_response(user, is_new_user=False)

        existing = await self.users.get_by_email(profile.email)
        if existing is not None:
            if not existing.is_active:
                raise AppException("Account is inactive", status_code=403)
            linked = await self._identity_for_user(existing.id)
            if linked is not None and linked.provider_subject != profile.subject:
                raise AppException("Google sign-in failed", status_code=409)
            if linked is None:
                await self._attach_identity(existing, profile)
            return self._auth_response(existing, is_new_user=False)

        user = await self._create_google_student(profile)
        return self._auth_response(user, is_new_user=True)

    async def me(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def logout(self) -> MessageResponse:
        return MessageResponse(message="Logged out successfully")

    def _auth_response(self, user: User, *, is_new_user: bool) -> AuthResponse:
        token = create_access_token(str(user.id), {"role": user.role.value})
        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=token,
            is_new_user=is_new_user,
        )

    async def _identity_by_subject(self, subject: str) -> UserAuthIdentity | None:
        result = await self.db.execute(
            select(UserAuthIdentity).where(
                UserAuthIdentity.provider == _GOOGLE,
                UserAuthIdentity.provider_subject == subject,
            )
        )
        return result.scalar_one_or_none()

    async def _identity_for_user(self, user_id) -> UserAuthIdentity | None:
        result = await self.db.execute(
            select(UserAuthIdentity).where(
                UserAuthIdentity.user_id == user_id,
                UserAuthIdentity.provider == _GOOGLE,
            )
        )
        return result.scalar_one_or_none()

    async def _attach_identity(self, user: User, profile: GoogleProfile) -> None:
        self.db.add(
            UserAuthIdentity(
                user_id=user.id,
                provider=_GOOGLE,
                provider_subject=profile.subject,
            )
        )
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppException("Google sign-in failed", status_code=409) from None

    async def _allocate_username(self, email: str, full_name: str | None) -> str:
        base = username_base(email, full_name)
        candidate = base
        number = 2
        while await self.users.get_by_username(candidate):
            suffix = str(number)
            candidate = f"{base[: 100 - len(suffix)]}{suffix}"
            number += 1
            if number > 1000:
                raise AppException("Could not create an account", status_code=500)
        return candidate

    async def _create_google_student(self, profile: GoogleProfile) -> User:
        username = await self._allocate_username(profile.email, profile.name)
        user = User(
            email=profile.email,
            username=username,
            full_name=profile.name,
            password_hash=None,
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        self.db.add(
            UserAuthIdentity(
                user_id=user.id,
                provider=_GOOGLE,
                provider_subject=profile.subject,
            )
        )
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            identity = await self._identity_by_subject(profile.subject)
            if identity is None:
                existing = await self.users.get_by_email(profile.email)
                if existing is None:
                    raise AppException("Google sign-in failed", status_code=409) from None
                return existing
            found = await self.users.get_by_id(identity.user_id)
            if found is None:
                raise AppException("Google sign-in failed", status_code=409) from None
            return found
        await self.db.refresh(user)
        return user
