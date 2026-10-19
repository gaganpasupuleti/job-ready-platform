"""Concise review and reply messages. Private note and ticket bodies are not inputs."""

from __future__ import annotations

import html
from uuid import UUID

from app.core.config import settings
from app.email.preferences import make_unsubscribe_token
from app.models.notification import ASSIGNMENT_REVIEW, ASSIGNMENT_REVIEW_MESSAGE, SUPPORT_REPLY_MESSAGE

_SUBJECTS = {
    "assignment_review": "Your assignment has been reviewed",
    "support_reply": "You have a new reply on your request",
}


def build_email(
    *,
    recipient_id: UUID,
    recipient_name: str,
    event_type: str,
    destination_path: str,
) -> tuple[str, str, str] | None:
    """Return subject, plain text, and HTML, or None when the public site URL is unusable."""
    base = settings.frontend_link_base
    if base is None or not destination_path.startswith("/"):
        return None
    subject = _SUBJECTS[event_type]
    summary = ASSIGNMENT_REVIEW_MESSAGE if event_type == "assignment_review" else SUPPORT_REPLY_MESSAGE
    destination = f"{base}{destination_path}"
    unsubscribe = f"{base}/email/unsubscribe?token={make_unsubscribe_token(recipient_id, event_type)}"
    name = recipient_name.strip() or "there"
    text = (
        f"Hello {name},\n\n"
        f"{summary}\n\n"
        f"Open it: {destination}\n\n"
        f"To stop these emails: {unsubscribe}\n"
    )
    safe_name = html.escape(name)
    safe_destination = html.escape(destination, quote=True)
    safe_unsubscribe = html.escape(unsubscribe, quote=True)
    safe_summary = html.escape(summary)
    html_body = (
        "<!DOCTYPE html><html><body>"
        f"<p>Hello {safe_name},</p>"
        f"<p>{safe_summary}</p>"
        f'<p><a href="{safe_destination}">Open it in JobReady</a></p>'
        f'<p><a href="{safe_unsubscribe}">Stop these emails</a></p>'
        "</body></html>"
    )
    return subject, text, html_body
