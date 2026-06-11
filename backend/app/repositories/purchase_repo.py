from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Purchase


def create(db: Session, **fields) -> Purchase:
    obj = Purchase(**fields)
    db.add(obj)
    db.flush()
    return obj


def list_for_target(db: Session, target_kind: str, target_id: int) -> list[Purchase]:
    rows = db.scalars(
        select(Purchase)
        .where(Purchase.target_kind == target_kind, Purchase.target_id == target_id)
        .order_by(Purchase.id)
    ).all()
    return list(rows)
