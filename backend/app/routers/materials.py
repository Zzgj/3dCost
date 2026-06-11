from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import material_repo
from app.responses import APIError, ok, ok_list
from app.schemas import MaterialCreate, MaterialOut, MaterialUpdate

router = APIRouter(prefix="/api/materials", tags=["materials"])


def _get_or_404(db: Session, material_id: int):
    obj = material_repo.get(db, material_id)
    if obj is None or not obj.is_active:
        raise APIError("NOT_FOUND", "耗材不存在", status_code=404)
    return obj


@router.post("")
def create_material(payload: MaterialCreate, db: Session = Depends(get_db)):
    obj = material_repo.create(db, **payload.model_dump())
    db.commit()
    db.refresh(obj)
    return ok(MaterialOut.model_validate(obj).model_dump(mode="json"))


@router.get("")
def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, total = material_repo.list_active(db, page, page_size)
    data = [MaterialOut.model_validate(r).model_dump(mode="json") for r in rows]
    return ok_list(data, page, page_size, total)


@router.get("/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, material_id)
    return ok(MaterialOut.model_validate(obj).model_dump(mode="json"))


@router.patch("/{material_id}")
def update_material(material_id: int, payload: MaterialUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, material_id)
    material_repo.update(db, obj, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(obj)
    return ok(MaterialOut.model_validate(obj).model_dump(mode="json"))


@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, material_id)
    material_repo.soft_delete(db, obj)
    db.commit()
    return ok({"deleted": material_id})
