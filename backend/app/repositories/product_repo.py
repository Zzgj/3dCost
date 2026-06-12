from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BOMItem, Product


def create(db: Session, bom_items: list[dict] | None = None, **fields) -> Product:
    obj = Product(**fields)
    db.add(obj)
    db.flush()
    if bom_items:
        for it in bom_items:
            db.add(BOMItem(product_id=obj.id, **it))
        db.flush()
    return obj


def get(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def list_active(
    db: Session, page: int, page_size: int, status: str | None = None, mode: str | None = None
) -> tuple[list[Product], int]:
    base = select(Product).where(Product.is_active.is_(True))
    if status:
        base = base.where(Product.status == status)
    if mode:
        base = base.where(Product.mode == mode)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def replace_bom(db: Session, obj: Product, bom_items: list[dict]) -> None:
    """替换 BOM：清空旧项（cascade delete-orphan），写入新项。

    直接操作 relationship 集合，确保内存中的 obj.bom_items 与库一致，
    后续成本装配读取的是最新 BOM。
    """
    obj.bom_items.clear()
    db.flush()
    for it in bom_items:
        obj.bom_items.append(BOMItem(**it))
    db.flush()


def update(db: Session, obj: Product, **fields) -> Product:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj


def soft_delete(db: Session, obj: Product) -> None:
    obj.is_active = False
    db.flush()
