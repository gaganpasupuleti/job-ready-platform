from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import get_token_subject
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppException("Not authenticated", status_code=401)

    try:
        user_id = get_token_subject(credentials.credentials)
    except JWTError as exc:
        raise AppException("Invalid or expired token", status_code=401) from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AppException("User not found or inactive", status_code=401)
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in {UserRole.ADMIN, UserRole.TRAINER}:
        raise AppException("Admin access required", status_code=403)
    return user


def require_roles(*roles: UserRole):
    async def _require(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppException("Insufficient permissions", status_code=403)
        return user

    return _require
