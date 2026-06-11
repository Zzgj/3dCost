from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import machine_repo
from app.responses import APIError, ok, ok_list
from app.schemas import MachineCreate, MachineOut, MachineUpdate

router = APIRouter(prefix="/api/machines", tags=["machines"])


def _get_or_404(db: Session, machine_id: int):
    obj = machine_repo.get(db, machine_id)
    if obj is None or not obj.is_active:
        raise APIError("NOT_FOUND", "机器不存在", status_code=404)
    return obj


@router.post("")
def create_machine(payload: MachineCreate, db: Session = Depends(get_db)):
    obj = machine_repo.create(db, **payload.model_dump())
    db.commit()
    db.refresh(obj)
    return ok(MachineOut.model_validate(obj).model_dump(mode="json"))


@router.get("")
def list_machines(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows, total = machine_repo.list_active(db, page, page_size)
    data = [MachineOut.model_validate(r).model_dump(mode="json") for r in rows]
    return ok_list(data, page, page_size, total)


@router.get("/{machine_id}")
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, machine_id)
    return ok(MachineOut.model_validate(obj).model_dump(mode="json"))


@router.patch("/{machine_id}")
def update_machine(machine_id: int, payload: MachineUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, machine_id)
    machine_repo.update(db, obj, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(obj)
    return ok(MachineOut.model_validate(obj).model_dump(mode="json"))
