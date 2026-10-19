"""Who may register or use a password. This module stores no passwords."""

from app.core.config import settings
from app.models.enums import UserRole

GOOGLE_ACCESS_DENIED = "This Google account does not have access. Contact your instructor."
REGISTRATION_CLOSED = "Registration is closed"


def registration_open() -> bool:
    if settings.public_registration_enabled is not None:
        return bool(settings.public_registration_enabled)
    return settings.app_env.lower() not in {"production", "prod"}


def password_login_permitted(email: str, role: UserRole) -> bool:
    if role == UserRole.ADMIN:
        return True
    allowed = {
        part.strip().lower()
        for part in settings.password_login_emails.split(",")
        if part.strip()
    }
    if allowed:
        return email.lower() in allowed
    return settings.app_env.lower() not in {"production", "prod"}
