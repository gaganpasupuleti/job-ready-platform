"""Retry session ids are validated before a practice session is created."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.mistake import RetrySessionRequest


def test_retry_schema_rejects_malformed_ids():
    with pytest.raises(ValidationError):
        RetrySessionRequest(question_ids=["not-a-uuid"])


def test_retry_schema_rejects_more_than_50_ids():
    ids = [str(uuid.uuid4()) for _ in range(51)]
    with pytest.raises(ValidationError):
        RetrySessionRequest(question_ids=ids)


@pytest.mark.asyncio
async def test_practice_and_mistake_retry_reject_malformed_ids(client, student_auth):
    headers, _email = student_auth
    payload = {"question_ids": ["not-a-uuid"]}
    practice = await client.post("/api/v1/practice/sessions/retry", headers=headers, json=payload)
    mistakes = await client.post("/api/v1/mistakes/retry-session", headers=headers, json=payload)
    assert practice.status_code == 422, practice.text
    assert mistakes.status_code == 422, mistakes.text
