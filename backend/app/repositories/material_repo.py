from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Material


def create(db: Session, **fields) -> Material:
    obj = Material(**fields)
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, material_id: int) -> Material | None:
    return db.get(Material, material_id)


def list_active(db: Session, page: int, page_size: int) -> tuple[list[Material], int]:
    base = select(Material).where(Material.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Material.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def update(db: Session, obj: Material, **fields) -> Material:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj


def soft_delete(db: Session, obj: Material) -> None:
    obj.is_active = False
    db.flush()
