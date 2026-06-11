from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Machine


def create(db: Session, **fields) -> Machine:
    obj = Machine(**fields)
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, machine_id: int) -> Machine | None:
    return db.get(Machine, machine_id)


def list_active(db: Session, page: int, page_size: int) -> tuple[list[Machine], int]:
    base = select(Machine).where(Machine.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Machine.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def update(db: Session, obj: Machine, **fields) -> Machine:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj
