from fastapi import APIRouter

from app.responses import APIError, ok
from app.schemas import BackupOut
from app.services import backups as backup_service

router = APIRouter(prefix="/api/backups", tags=["backups"])


def _dump(info: dict) -> dict:
    return BackupOut.model_validate(info).model_dump(mode="json")


@router.post("")
def create_backup():
    try:
        return ok(_dump(backup_service.create_backup()))
    except FileNotFoundError as exc:
        raise APIError("BACKUP_FAILED", str(exc), status_code=400) from exc


@router.get("")
def list_backups():
    return ok([_dump(item) for item in backup_service.list_backups()])
