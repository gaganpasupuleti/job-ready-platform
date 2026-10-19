from pydantic import BaseModel


class EmailPreferences(BaseModel):
    assignment_review_enabled: bool
    support_reply_enabled: bool


class EmailPreferenceUpdate(BaseModel):
    assignment_review_enabled: bool | None = None
    support_reply_enabled: bool | None = None


class EmailUnsubscribeRequest(BaseModel):
    token: str
