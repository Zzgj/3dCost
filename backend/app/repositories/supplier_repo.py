from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Supplier


def create(db: Session, **fields) -> Supplier:
    obj = Supplier(**fields)
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, supplier_id: int) -> Supplier | None:
    return db.get(Supplier, supplier_id)


def list_active(db: Session, page: int, page_size: int) -> tuple[list[Supplier], int]:
    base = select(Supplier).where(Supplier.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Supplier.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def update(db: Session, obj: Supplier, **fields) -> Supplier:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj


def soft_delete(db: Session, obj: Supplier) -> None:
    obj.is_active = False
    db.flush()
