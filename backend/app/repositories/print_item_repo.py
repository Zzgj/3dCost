from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import PrintFilament, PrintItem


def create(db: Session, filaments: list[dict], **fields) -> PrintItem:
    """filaments: [{"material_id": int, "grams": Decimal}, ...]"""
    obj = PrintItem(**fields)
    obj.filaments = [
        PrintFilament(material_id=f["material_id"], grams=f["grams"]) for f in filaments
    ]
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, print_item_id: int) -> PrintItem | None:
    return db.scalar(
        select(PrintItem)
        .where(PrintItem.id == print_item_id)
        .options(selectinload(PrintItem.filaments))
    )


def list_active(db: Session, page: int, page_size: int) -> tuple[list[PrintItem], int]:
    base = select(PrintItem).where(PrintItem.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.options(selectinload(PrintItem.filaments))
        .order_by(PrintItem.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total


def update(db: Session, obj: PrintItem, filaments: list[dict] | None = None, **fields) -> PrintItem:
    for key, value in fields.items():
        setattr(obj, key, value)
    if filaments is not None:
        obj.filaments = [
            PrintFilament(material_id=f["material_id"], grams=f["grams"]) for f in filaments
        ]
    db.flush()
    return obj


def soft_delete(db: Session, obj: PrintItem) -> None:
    obj.is_active = False
    db.flush()
