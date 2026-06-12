from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Part, PrintItem, Product
from app.repositories import product_repo
from app.responses import APIError, ok, ok_list
from app.schemas import ProductCreate, ProductDetailOut, ProductOut, ProductUpdate
from app.services import cost_assembler
from app.services.bom_validator import BOMCycleError
from app.services.inventory import InsufficientStockError, consume_stock_for_product

router = APIRouter(prefix="/api/products", tags=["products"])


def _get_or_404(db: Session, product_id: int) -> Product:
    obj = product_repo.get(db, product_id)
    if obj is None or not obj.is_active:
        raise APIError("NOT_FOUND", "产品不存在", status_code=404)
    return obj


def _ref_name(db: Session, kind: str, ref_id: int | None) -> str | None:
    if ref_id is None:
        return None
    if kind == "printitem":
        obj = db.get(PrintItem, ref_id)
    elif kind == "part":
        obj = db.get(Part, ref_id)
    elif kind == "subproduct":
        obj = db.get(Product, ref_id)
    else:
        return None
    return obj.name if obj else None


def _serialize(db: Session, product: Product) -> dict:
    """计算成本、写回快照、组装 ProductDetailOut（含 bom_items + cost_detail）。"""
    try:
        detail, snapshots = cost_assembler.assemble_product_cost(db, product)
    except BOMCycleError as exc:
        raise APIError("BOM_CYCLE_DETECTED", str(exc), status_code=400) from exc
    snap_by_id = {s["id"]: s for s in snapshots}
    for it in product.bom_items:
        s = snap_by_id.get(it.id)
        if s:
            it.unit_price = s["unit_price"]
            it.subtotal = s["subtotal"]
    product.total_cost = detail["total_cost"]
    product.customer_price = detail["customer_price"]
    db.flush()

    bom_out = []
    for it in product.bom_items:
        bom_out.append(
            {
                "id": it.id,
                "kind": it.kind,
                "ref_id": it.ref_id,
                "ref_name": _ref_name(db, it.kind, it.ref_id),
                "qty": it.qty,
                "hours": it.hours,
                "unit_price": it.unit_price,
                "subtotal": it.subtotal,
            }
        )
    base = ProductOut.model_validate(product).model_dump()
    detail_out = ProductDetailOut.model_validate(
        {**base, "bom_items": bom_out, "cost_detail": detail}
    )
    return detail_out.model_dump(mode="json")


@router.post("")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    bom = [it.model_dump() for it in payload.bom_items]
    obj = product_repo.create(
        db,
        bom_items=bom,
        name=payload.name,
        note=payload.note,
        mode=payload.mode,
        markup_rate=payload.markup_rate,
    )
    try:
        data = _serialize(db, obj)
    except APIError:
        db.rollback()
        raise
    db.commit()
    return ok(data)


@router.get("")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    mode: str | None = Query(None),
    db: Session = Depends(get_db),
):
    rows, total = product_repo.list_active(db, page, page_size, status, mode)
    data = [_serialize(db, r) for r in rows]
    db.commit()
    return ok_list(data, page, page_size, total)


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, product_id)
    data = _serialize(db, obj)
    db.commit()
    return ok(data)


@router.patch("/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, product_id)
    if obj.status == "completed":
        raise APIError("LOCKED_RESOURCE", "产品已完成，禁止修改", status_code=409)
    fields = payload.model_dump(exclude_unset=True)
    bom = fields.pop("bom_items", None)
    if fields:
        product_repo.update(db, obj, **fields)
    if bom is not None:
        product_repo.replace_bom(db, obj, bom)
    try:
        data = _serialize(db, obj)
    except APIError:
        db.rollback()
        raise
    db.commit()
    return ok(data)


@router.post("/{product_id}/consume-stock")
def consume_stock(product_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, product_id)
    try:
        result = consume_stock_for_product(db, obj)
    except InsufficientStockError as exc:
        db.rollback()
        raise APIError(
            "INSUFFICIENT_STOCK", str(exc), status_code=400, details=exc.details
        ) from exc
    db.commit()
    return ok(result, warnings=result["warnings"])


@router.post("/{product_id}/complete")
def complete_product(product_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, product_id)
    obj.status = "completed"
    db.flush()
    data = _serialize(db, obj)
    db.commit()
    return ok(data)
