from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import part_repo
from app.responses import APIError, ok, ok_list
from app.schemas import PartCreate, PartOut, PartUpdate

router = APIRouter(prefix="/api/parts", tags=["parts"])


def _get_or_404(db: Session, part_id: int):
    obj = part_repo.get(db, part_id)
    if obj is None or not obj.is_active:
        raise APIError("NOT_FOUND", "零件不存在", status_code=404)
    return obj


@router.post("")
def create_part(payload: PartCreate, db: Session = Depends(get_db)):
    obj = part_repo.create(db, **payload.model_dump())
    db.commit()
    db.refresh(obj)
    return ok(PartOut.model_validate(obj).model_dump(mode="json"))


@router.get("")
def list_parts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    rows, total = part_repo.list_active(db, page, page_size, search, category)
    data = [PartOut.model_validate(r).model_dump(mode="json") for r in rows]
    return ok_list(data, page, page_size, total)


@router.get("/{part_id}")
def get_part(part_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, part_id)
    return ok(PartOut.model_validate(obj).model_dump(mode="json"))


@router.patch("/{part_id}")
def update_part(part_id: int, payload: PartUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, part_id)
    part_repo.update(db, obj, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(obj)
    return ok(PartOut.model_validate(obj).model_dump(mode="json"))


@router.delete("/{part_id}")
def delete_part(part_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, part_id)
    part_repo.soft_delete(db, obj)
    db.commit()
    return ok({"deleted": part_id})
