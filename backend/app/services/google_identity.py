"""Verify a Google Identity Services ID token. Never log the credential."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleTokenError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class GoogleProfile:
    subject: str
    email: str
    name: str | None


def _looks_like_jwt(credential: str) -> bool:
    parts = credential.split(".")
    return len(parts) == 3 and all(part.strip() for part in parts)


def _decode_with_google(credential: str, client_id: str) -> dict[str, Any]:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    claims = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    if not isinstance(claims, dict):
        raise GoogleTokenError("invalid")
    return claims


def _profile_from_claims(claims: dict[str, Any], client_id: str) -> GoogleProfile:
    issuer = str(claims.get("iss") or "")
    if issuer not in _GOOGLE_ISSUERS:
        raise GoogleTokenError("issuer")
    audience = claims.get("aud")
    if audience != client_id:
        raise GoogleTokenError("audience")
    if claims.get("email_verified") is not True:
        raise GoogleTokenError("unverified")
    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    if not subject or not email or "@" not in email:
        raise GoogleTokenError("missing")
    name = claims.get("name")
    return GoogleProfile(subject=subject, email=email, name=str(name).strip() if name else None)


def verify_google_id_token(
    credential: str,
    client_id: str,
    *,
    decode: Callable[[str, str], dict[str, Any]] | None = None,
) -> GoogleProfile:
    if not client_id or not client_id.strip():
        raise GoogleTokenError("unconfigured")
    if not isinstance(credential, str) or not _looks_like_jwt(credential.strip()):
        raise GoogleTokenError("malformed")
    decoder = decode or _decode_with_google
    try:
        claims = decoder(credential.strip(), client_id.strip())
    except GoogleTokenError:
        raise
    except Exception as exc:
        reason = "expired" if "expired" in str(exc).lower() else "invalid"
        raise GoogleTokenError(reason) from exc
    return _profile_from_claims(claims, client_id.strip())
