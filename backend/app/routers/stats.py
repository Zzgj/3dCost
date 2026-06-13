from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Material, Part, PrintItem, Product
from app.responses import ok
from app.schemas import LowStockOut, MaterialUsageOut, MonthlyStatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db)):
    materials = db.scalars(
        select(Material).where(
            Material.is_active.is_(True),
            Material.low_stock_g > 0,
            Material.stock_g < Material.low_stock_g,
        )
    ).all()
    parts = db.scalars(
        select(Part).where(
            Part.is_active.is_(True),
            Part.low_stock_qty > 0,
            Part.stock_qty < Part.low_stock_qty,
        )
    ).all()
    data = LowStockOut(
        materials=[
            {
                "id": m.id,
                "name": m.name,
                "stock_g": m.stock_g,
                "low_stock_g": m.low_stock_g,
                "avg_price_per_g": m.avg_price_per_g,
            }
            for m in materials
        ],
        parts=[
            {
                "id": p.id,
                "name": p.name,
                "stock_qty": p.stock_qty,
                "low_stock_qty": p.low_stock_qty,
                "avg_unit_price": p.avg_unit_price,
                "use_unit": p.use_unit,
            }
            for p in parts
        ],
    )
    return ok(data.model_dump(mode="json"))


@router.get("/monthly")
def monthly(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Product).where(
            Product.is_active.is_(True),
            extract("year", Product.created_at) == year,
            extract("month", Product.created_at) == month,
        )
    ).all()
    total_cost = sum((p.total_cost for p in rows), Decimal("0"))
    customer_price = sum((p.customer_price for p in rows), Decimal("0"))
    data = MonthlyStatsOut(
        year=year,
        month=month,
        products_count=len(rows),
        completed_count=sum(1 for p in rows if p.status == "completed"),
        total_cost=total_cost,
        customer_price=customer_price,
        estimated_profit=customer_price - total_cost,
    )
    return ok(data.model_dump(mode="json"))


@router.get("/material-usage")
def material_usage(
    start: date | None = Query(None),
    end: date | None = Query(None),
    db: Session = Depends(get_db),
):
    query = select(Product).where(Product.is_active.is_(True), Product.status == "completed")
    if start is not None:
        query = query.where(Product.updated_at >= start)
    if end is not None:
        query = query.where(Product.updated_at < end)
    products = db.scalars(query).all()

    usage: dict[int, Decimal] = {}
    for product in products:
        for item in product.bom_items:
            if item.kind != "printitem" or item.ref_id is None:
                continue
            qty = item.qty or Decimal("1")
            print_item = db.get(PrintItem, item.ref_id)
            if print_item is None:
                continue
            for filament in print_item.filaments:
                usage[filament.material_id] = usage.get(filament.material_id, Decimal("0")) + filament.grams * qty

    data = []
    for material_id, grams in sorted(usage.items()):
        material = db.get(Material, material_id)
        data.append(
            MaterialUsageOut(
                material_id=material_id,
                material_name=material.name if material else f"#{material_id}",
                grams=grams,
            ).model_dump(mode="json")
        )
    return ok(data)
