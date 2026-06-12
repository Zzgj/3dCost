from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models import CostSetting, Machine, Material, Part, PrintItem, Product
from app.repositories import product_repo, settings_repo
from app.responses import APIError
from app.services import bom_validator, costing

_QUANT_2 = Decimal("0.01")


def _r2(v: Decimal) -> Decimal:
    return v.quantize(_QUANT_2, rounding=ROUND_HALF_UP)


def assemble_print_item_cost(db: Session, print_item: PrintItem) -> dict[str, Decimal]:
    """从 DB 装配打印件成本所需数据并计算成本。缺机器或机器已停用时抛 COST_SOURCE_MISSING。"""
    machine = db.get(Machine, print_item.machine_id)
    if machine is None or not machine.is_active:
        raise APIError(
            "COST_SOURCE_MISSING", "打印件关联的机器不存在或已停用", status_code=400,
            details={"machine_id": print_item.machine_id},
        )

    filament_rows: list[tuple[Decimal, Decimal]] = []
    for f in print_item.filaments:
        material = db.get(Material, f.material_id)
        price = material.avg_price_per_g if material else Decimal("0")
        filament_rows.append((f.grams, price))

    setting = settings_repo.get_or_default(db)
    return costing.calc_print_item_cost(
        filaments=filament_rows,
        print_hours=print_item.print_hours,
        machine_price=machine.price,
        machine_life_hours=machine.life_hours,
        machine_power_w=machine.power_w,
        electricity_price=setting.electricity_price,
    )


def _build_subproduct_edges(db: Session, root: Product) -> dict[int, list[int]]:
    """从 root 出发，构建产品ID → 直接子产品ID列表的引用图。"""
    edges: dict[int, list[int]] = {}
    stack = [root.id]
    while stack:
        pid = stack.pop()
        if pid in edges:
            continue
        prod = product_repo.get(db, pid)
        if prod is None:
            edges[pid] = []
            continue
        children = [
            it.ref_id
            for it in prod.bom_items
            if it.kind == "subproduct" and it.ref_id is not None
        ]
        edges[pid] = children
        stack.extend(children)
    return edges


def _resolve_product_total(db: Session, product: Product, settings: CostSetting) -> Decimal:
    """递归解析子产品 total_cost（循环已在外层检测）。"""
    _, detail = _assemble(db, product, settings)
    return detail["total_cost"]


def _assemble(db: Session, product: Product, settings: CostSetting) -> tuple[list[dict], dict]:
    """返回 (bom_snapshots, cost_detail)。bom_snapshots 含每项 unit_price/subtotal。"""
    bom_calc_items: list[dict] = []
    snapshots: list[dict] = []
    for it in product.bom_items:
        if it.kind == "printitem":
            pi = db.get(PrintItem, it.ref_id)
            unit_price = assemble_print_item_cost(db, pi)["total"]
            qty = it.qty or Decimal("1")
            bom_calc_items.append({"kind": "printitem", "unit_price": unit_price, "qty": qty})
            snapshots.append({"id": it.id, "unit_price": _r2(unit_price), "subtotal": _r2(unit_price * qty)})
        elif it.kind == "part":
            part = db.get(Part, it.ref_id)
            unit_price = part.avg_unit_price if part else Decimal("0")
            qty = it.qty or Decimal("1")
            bom_calc_items.append({"kind": "part", "unit_price": unit_price, "qty": qty})
            snapshots.append({"id": it.id, "unit_price": _r2(unit_price), "subtotal": _r2(unit_price * qty)})
        elif it.kind == "postprocess":
            hours = it.hours or Decimal("0")
            bom_calc_items.append({"kind": "postprocess", "hours": hours})
            snapshots.append(
                {"id": it.id, "unit_price": _r2(settings.labor_rate), "subtotal": _r2(settings.labor_rate * hours)}
            )
        elif it.kind == "subproduct":
            child = product_repo.get(db, it.ref_id)
            unit_price = _resolve_product_total(db, child, settings) if child else Decimal("0")
            qty = it.qty or Decimal("1")
            bom_calc_items.append({"kind": "subproduct", "unit_price": unit_price, "qty": qty})
            snapshots.append({"id": it.id, "unit_price": _r2(unit_price), "subtotal": _r2(unit_price * qty)})

    detail = costing.calc_product_cost(
        bom_items=bom_calc_items,
        markup_rate=product.markup_rate,
        labor_rate=settings.labor_rate,
        scrap_rate=settings.scrap_rate,
    )
    return snapshots, detail


def assemble_product_cost(db: Session, product: Product) -> tuple[dict, list[dict]]:
    """装配产品成本：先循环检测，再自底向上算成本。

    返回 (cost_detail, bom_snapshots)。
    """
    edges = _build_subproduct_edges(db, product)
    bom_validator.check_bom_cycle(product.id, edges)
    settings = settings_repo.get_or_default(db)
    snapshots, detail = _assemble(db, product, settings)
    return detail, snapshots
