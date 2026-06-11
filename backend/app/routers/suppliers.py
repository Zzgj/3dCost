from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import supplier_repo
from app.responses import APIError, ok, ok_list
from app.schemas import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


def _get_or_404(db: Session, supplier_id: int):
    obj = supplier_repo.get(db, supplier_id)
    if obj is None or not obj.is_active:
        raise APIError("NOT_FOUND", "供应商不存在", status_code=404)
    return obj


@router.post("")
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    obj = supplier_repo.create(db, **payload.model_dump())
    db.commit()
    db.refresh(obj)
    return ok(SupplierOut.model_validate(obj).model_dump(mode="json"))


@router.get("")
def list_suppliers(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows, total = supplier_repo.list_active(db, page, page_size)
    data = [SupplierOut.model_validate(r).model_dump(mode="json") for r in rows]
    return ok_list(data, page, page_size, total)


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, supplier_id)
    return ok(SupplierOut.model_validate(obj).model_dump(mode="json"))


@router.patch("/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, supplier_id)
    supplier_repo.update(db, obj, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(obj)
    return ok(SupplierOut.model_validate(obj).model_dump(mode="json"))


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, supplier_id)
    supplier_repo.soft_delete(db, obj)
    db.commit()
    return ok({"deleted": supplier_id})
