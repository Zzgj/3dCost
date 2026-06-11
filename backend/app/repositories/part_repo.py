from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Part


def create(db: Session, **fields) -> Part:
    obj = Part(**fields)
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, part_id: int) -> Part | None:
    return db.get(Part, part_id)


def list_active(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    category: str | None = None,
) -> tuple[list[Part], int]:
    base = select(Part).where(Part.is_active.is_(True))
    if search:
        base = base.where(Part.name.contains(search))
    if category:
        base = base.where(Part.category == category)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Part.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def update(db: Session, obj: Part, **fields) -> Part:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj


def soft_delete(db: Session, obj: Part) -> None:
    obj.is_active = False
    db.flush()
