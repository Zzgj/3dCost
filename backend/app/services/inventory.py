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


# ---------- 产品库存扣减 ----------
from app.models import PrintItem, Product  # noqa: E402


class InsufficientStockError(Exception):
    """库存不足，无法扣减。"""

    def __init__(self, message: str, details: dict):
        self.details = details
        super().__init__(message)


def _material_demand(db: Session, product: Product) -> dict[int, Decimal]:
    """汇总产品 BOM 中所有打印件 filaments 的耗材需求（material_id → 总克数）。"""
    demand: dict[int, Decimal] = {}
    for it in product.bom_items:
        if it.kind != "printitem" or it.ref_id is None:
            continue
        qty = it.qty or Decimal("1")
        pi = db.get(PrintItem, it.ref_id)
        if pi is None:
            continue
        for f in pi.filaments:
            demand[f.material_id] = demand.get(f.material_id, Decimal("0")) + f.grams * qty
    return demand


def _part_demand(product: Product) -> dict[int, Decimal]:
    """汇总产品 BOM 中零件需求（part_id → 总数量）。"""
    demand: dict[int, Decimal] = {}
    for it in product.bom_items:
        if it.kind != "part" or it.ref_id is None:
            continue
        demand[it.ref_id] = demand.get(it.ref_id, Decimal("0")) + (it.qty or Decimal("1"))
    return demand


def consume_stock_for_product(db: Session, product: Product) -> dict:
    """单事务内按 BOM 扣减耗材与零件。先全量校验，任一不足抛 InsufficientStockError 不做扣减。

    调用方负责 commit/rollback。返回 {"consumed": {...}, "warnings": [...]}。
    """
    mat_demand = _material_demand(db, product)
    part_demand = _part_demand(product)

    # 1. 全量校验
    materials: dict[int, Material] = {}
    for mid, need in mat_demand.items():
        m = db.get(Material, mid)
        if m is None or m.stock_g < need:
            raise InsufficientStockError(
                "耗材库存不足",
                {
                    "material_id": mid,
                    "required_g": str(need),
                    "stock_g": str(m.stock_g if m else 0),
                },
            )
        materials[mid] = m
    parts: dict[int, Part] = {}
    for pid, need in part_demand.items():
        p = db.get(Part, pid)
        if p is None or p.stock_qty < need:
            raise InsufficientStockError(
                "零件库存不足",
                {
                    "part_id": pid,
                    "required_qty": str(need),
                    "stock_qty": str(p.stock_qty if p else 0),
                },
            )
        parts[pid] = p

    # 2. 校验通过，统一扣减
    consumed: dict[str, list] = {"materials": [], "parts": []}
    warnings: list[str] = []
    for mid, need in mat_demand.items():
        m = materials[mid]
        m.stock_g -= need
        consumed["materials"].append(
            {"name": m.name, "deducted_g": str(need), "remaining_g": str(m.stock_g)}
        )
        if m.stock_g < m.low_stock_g:
            warnings.append(f"{m.name} 低于库存阈值")
    for pid, need in part_demand.items():
        p = parts[pid]
        p.stock_qty -= need
        consumed["parts"].append(
            {"name": p.name, "deducted_qty": str(need), "remaining_qty": str(p.stock_qty)}
        )
        if p.stock_qty < p.low_stock_qty:
            warnings.append(f"{p.name} 低于库存阈值")
    db.flush()
    return {"consumed": consumed, "warnings": warnings}
