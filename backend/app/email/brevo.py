"""Brevo transactional send adapter.

Official endpoint: POST https://api.brevo.com/v3/smtp/email
Headers: api-key, accept: application/json, content-type: application/json.
A 201 response body contains messageId. That id means Brevo accepted the
request. Delivery events are separate and are not read here.

The single-send reference does not document an HTTP Idempotency-Key that
suppresses a second POST of the same message. A custom headers.idempotencyKey
field appears in a batch example as an email header, not as a deduplication
contract. This adapter therefore sends the outbox id only as X-JobReady-Event
so a message can be correlated. A timeout or connection error is ambiguous:
Brevo may already have accepted it, and a retry could deliver a second copy.
The worker does not retry those outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx

from app.core.config import settings

SEND_URL = "https://api.brevo.com/v3/smtp/email"
Outcome = Literal["accepted", "retryable", "rejected", "ambiguous"]
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class SendResult:
    outcome: Outcome
    message_id: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class OutboundEmail:
    outbox_id: str
    recipient_email: str
    recipient_name: str
    subject: str
    text_body: str
    html_body: str


def safe_reason(reason: str) -> str:
    """Keep stored reasons to short codes. Never persist response bodies or secrets."""
    allowed = {
        "provider_timeout",
        "provider_connection",
        "missing_message_id",
        "provider_error",
        "http_429",
        "http_500",
        "http_502",
        "http_503",
        "http_504",
    }
    if reason in allowed or (reason.startswith("http_") and reason[5:].isdigit() and len(reason) <= 12):
        return reason
    return "provider_error"


class BrevoClient:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    async def send(self, message: OutboundEmail) -> SendResult:
        if not settings.email_can_send:
            return SendResult("rejected", reason="email_disabled")
        payload = {
            "sender": {
                "email": settings.email_from_address.strip(),
                "name": (settings.email_from_name or "JobReady").strip() or "JobReady",
            },
            "to": [{"email": message.recipient_email, "name": message.recipient_name or message.recipient_email}],
            "subject": message.subject,
            "textContent": message.text_body,
            "htmlContent": message.html_body,
            "headers": {"X-JobReady-Event": message.outbox_id},
        }
        try:
            async with httpx.AsyncClient(
                timeout=settings.email_http_timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    SEND_URL,
                    headers={
                        "api-key": settings.brevo_api_key,
                        "accept": "application/json",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
        except httpx.TimeoutException:
            return SendResult("ambiguous", reason="provider_timeout")
        except httpx.TransportError:
            return SendResult("ambiguous", reason="provider_connection")
        if response.status_code == 201:
            message_id = _message_id(response)
            if not message_id:
                return SendResult("ambiguous", reason="missing_message_id")
            return SendResult("accepted", message_id=message_id[:255], reason="accepted")
        if response.status_code in _RETRYABLE_STATUS:
            return SendResult("retryable", reason=f"http_{response.status_code}")
        if response.status_code == 408:
            return SendResult("ambiguous", reason="provider_timeout")
        if 400 <= response.status_code < 500:
            return SendResult("rejected", reason=f"http_{response.status_code}")
        return SendResult("ambiguous", reason="provider_error")


def _message_id(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return ""
    if not isinstance(body, dict):
        return ""
    value = body.get("messageId")
    return value.strip() if isinstance(value, str) else ""
