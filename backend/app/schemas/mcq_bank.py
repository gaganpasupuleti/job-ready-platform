from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import McqImportMode


class McqBankMeta(BaseModel):
    bank_key: str
    version: int
    question_count: int
    last_published_at: str | None = None


class McqImportPreview(BaseModel):
    added: list[dict] = Field(default_factory=list)
    updated: list[dict] = Field(default_factory=list)
    unchanged: list[dict] = Field(default_factory=list)
    archived: list[dict] = Field(default_factory=list)
    invalid_cross_bank: list[dict] = Field(default_factory=list)
    can_publish: bool
    blocking_reasons: list[str] = Field(default_factory=list)


class McqStageUploadResponse(BaseModel):
    import_run_id: UUID
    bank_key: str
    import_mode: McqImportMode
    workbook_checksum: str
    bank_version_at_preview: int
    can_publish: bool
    preview: McqImportPreview
    errors: list[dict] = Field(default_factory=list)


class McqPublishRequest(BaseModel):
    import_run_id: UUID


class McqPublishResponse(BaseModel):
    import_run_id: UUID
    bank_key: str
    bank_version: int
    published_at: str
    summary: McqImportPreview


class McqImportHistoryItem(BaseModel):
    id: UUID
    bank_key: str
    import_mode: str
    status: str
    created_at: str
    published_at: str | None = None
    error_count: int
    preview_summary: dict
