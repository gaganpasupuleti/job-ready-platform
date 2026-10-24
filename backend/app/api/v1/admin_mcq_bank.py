from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.enums import McqImportMode
from app.models.user import User
from app.schemas.mcq_bank import McqPublishRequest, McqPublishResponse, McqStageUploadResponse
from app.services.mcq_bank_service import McqBankService

router = APIRouter(prefix="/admin/mcq-bank")


@router.get("/banks")
async def list_banks(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await McqBankService(db).list_banks()


@router.get("/banks/{bank_key}")
async def get_bank_meta(
    bank_key: str,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await McqBankService(db).get_bank_meta(bank_key)


@router.get("/template")
async def download_template(
    bank_key: str = Query(..., min_length=2, max_length=80),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = McqBankService(db)
    taxonomy_rows = (await service.list_taxonomy_rows())[:200]
    data = service.build_template_bytes(bank_key, taxonomy_rows)
    filename = f"jobready-mcq-{bank_key}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export")
async def export_bank(
    bank_key: str = Query(..., min_length=2, max_length=80),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await McqBankService(db).export_bank(bank_key)
    filename = f"jobready-mcq-export-{bank_key}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import/stage", response_model=McqStageUploadResponse)
async def stage_import(
    bank_key: str = Form(...),
    import_mode: McqImportMode = Form(default=McqImportMode.ADD_UPDATE),
    allow_empty_replace: bool = Form(default=False),
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        from app.core.exceptions import AppException

        raise AppException("Only .xlsx workbooks are supported", status_code=400)
    data = await file.read()
    result = await McqBankService(db).stage_upload(
        admin,
        bank_key=bank_key.strip(),
        import_mode=import_mode,
        data=data,
        allow_empty_replace=allow_empty_replace,
    )
    return McqStageUploadResponse(**result)


@router.post("/import/publish", response_model=McqPublishResponse)
async def publish_import(
    payload: McqPublishRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await McqBankService(db).publish(admin, payload.import_run_id)
    return McqPublishResponse(**result)


@router.post("/import/{import_run_id}/rollback")
async def rollback_import(
    import_run_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await McqBankService(db).rollback(admin, import_run_id)


@router.get("/import/history")
async def import_history(
    bank_key: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await McqBankService(db).list_import_history(bank_key=bank_key, limit=limit)
