from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Quote


def create(db: Session, **fields) -> Quote:
    obj = Quote(**fields)
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, quote_id: int) -> Quote | None:
    return db.get(Quote, quote_id)


def list_quotes(
    db: Session,
    page: int,
    page_size: int,
    product_id: int | None = None,
) -> tuple[list[Quote], int]:
    base = select(Quote)
    if product_id is not None:
        base = base.where(Quote.product_id == product_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Quote.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total
