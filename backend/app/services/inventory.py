from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models import Material, Part
from app.repositories import purchase_repo
from app.services.pricing import (
    material_total_grams,
    part_total_use_qty,
    weighted_avg_price,
)

QUANT_QTY = Decimal("0.001")  # 数量列 Numeric(12,3)


def _quant_qty(value: Decimal) -> Decimal:
    return value.quantize(QUANT_QTY, rounding=ROUND_HALF_UP)


def record_material_purchase(
    db: Session,
    material: Material,
    qty_rolls: int,
    grams_per_roll: int,
    goods_amount: Decimal,
    shipping_fee: Decimal,
    supplier_id: int | None,
    purchase_url: str | None,
    purchased_at: datetime | None,
) -> dict:
    """录入耗材采购：写采购、加库存、重算到手价。调用方负责 commit。"""
    purchase_repo.create(
        db,
        target_kind="material",
        target_id=material.id,
        qty_rolls=qty_rolls,
        grams_per_roll=grams_per_roll,
        goods_amount=goods_amount,
        shipping_fee=shipping_fee,
        supplier_id=supplier_id,
        purchase_url=purchase_url,
        purchased_at=purchased_at or datetime.utcnow(),
    )
    rows = purchase_repo.list_for_target(db, "material", material.id)
    total_amount = sum((r.goods_amount + r.shipping_fee for r in rows), Decimal("0"))
    total_grams = _quant_qty(
        material_total_grams([(r.qty_rolls, r.grams_per_roll) for r in rows])
    )
    material.stock_g = _quant_qty(total_grams)
    material.avg_price_per_g = weighted_avg_price(total_amount, total_grams)
    db.flush()
    return {
        "updated_avg_price": material.avg_price_per_g,
        "total_stock": material.stock_g,
    }


def record_part_purchase(
    db: Session,
    part: Part,
    qty: Decimal,
    goods_amount: Decimal,
    shipping_fee: Decimal,
    supplier_id: int | None,
    purchase_url: str | None,
    purchased_at: datetime | None,
) -> dict:
    """录入零件采购：写采购、加库存（换算使用单位）、重算到手价。调用方负责 commit。"""
    purchase_repo.create(
        db,
        target_kind="part",
        target_id=part.id,
        qty=qty,
        goods_amount=goods_amount,
        shipping_fee=shipping_fee,
        supplier_id=supplier_id,
        purchase_url=purchase_url,
        purchased_at=purchased_at or datetime.utcnow(),
    )
    rows = purchase_repo.list_for_target(db, "part", part.id)
    total_amount = sum((r.goods_amount + r.shipping_fee for r in rows), Decimal("0"))
    total_use = part_total_use_qty([(r.qty, part.conversion_ratio) for r in rows])
    part.stock_qty = _quant_qty(total_use)
    part.avg_unit_price = weighted_avg_price(total_amount, total_use)
    db.flush()
    return {
        "updated_avg_price": part.avg_unit_price,
        "total_stock": part.stock_qty,
    }
