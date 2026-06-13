import json
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.repositories import quote_repo
from app.responses import APIError, ok, ok_list
from app.routers.products import _get_or_404 as get_product_or_404
from app.routers.products import _serialize as serialize_product
from app.schemas import QuoteCreate, QuoteDetailOut, QuoteOut
from app.services.quote_render import render_quote_html

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


KIND_LABELS = {
    "printitem": "打印件",
    "part": "零件",
    "postprocess": "后处理",
    "subproduct": "子产品",
}


def _decimal(value: str) -> Decimal:
    return Decimal(value)


def _snapshot_from_product(data: dict, quote_id: int | None = None) -> dict:
    bom_items = []
    for item in data["bom_items"]:
        bom_items.append({**item, "kind_label": KIND_LABELS.get(item["kind"], item["kind"])})
    return {
        "quote_id": quote_id,
        "created_at": datetime.utcnow().isoformat(),
        "product": {
            "id": data["id"],
            "name": data["name"],
            "mode": data["mode"],
            "status": data["status"],
            "markup_rate": data["markup_rate"],
            "note": data["note"],
        },
        "cost_detail": data["cost_detail"],
        "bom_items": bom_items,
    }


def _quote_out(obj, snapshot: dict | None = None) -> dict:
    base = QuoteOut.model_validate(obj).model_dump(mode="json")
    if snapshot is None:
        try:
            snapshot = json.loads(obj.snapshot_json)
        except json.JSONDecodeError:
            snapshot = None
    if snapshot is not None:
        base["internal_cost"] = snapshot["cost_detail"]["total_cost"]
        base["customer_price"] = snapshot["cost_detail"]["customer_price"]
    if snapshot is None:
        return base
    return QuoteDetailOut.model_validate({**base, "snapshot": snapshot}).model_dump(mode="json")


@router.post("")
def create_quote(payload: QuoteCreate, db: Session = Depends(get_db)):
    product = get_product_or_404(db, payload.product_id)
    product_data = serialize_product(db, product)
    quote_mode = payload.mode or product_data["mode"]
    product_data["mode"] = quote_mode
    snapshot = _snapshot_from_product(product_data)
    obj = quote_repo.create(
        db,
        product_id=product.id,
        mode=quote_mode,
        internal_cost=_decimal(product_data["cost_detail"]["total_cost"]),
        customer_price=_decimal(product_data["cost_detail"]["customer_price"]),
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
    snapshot["quote_id"] = obj.id
    obj.snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    db.commit()
    db.refresh(obj)
    return ok(_quote_out(obj, snapshot))


@router.get("")
def list_quotes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    rows, total = quote_repo.list_quotes(db, page, page_size, product_id)
    return ok_list([_quote_out(r) for r in rows], page, page_size, total)


@router.get("/{quote_id}")
def get_quote(quote_id: int, db: Session = Depends(get_db)):
    obj = quote_repo.get(db, quote_id)
    if obj is None:
        raise APIError("NOT_FOUND", "报价不存在", status_code=404)
    return ok(_quote_out(obj, json.loads(obj.snapshot_json)))


@router.get("/{quote_id}/export")
def export_quote(
    quote_id: int,
    type: str = Query("customer", pattern="^(internal|customer)$"),
    format: str = Query("html", pattern="^(html|pdf|png)$"),
    db: Session = Depends(get_db),
):
    obj = quote_repo.get(db, quote_id)
    if obj is None:
        raise APIError("NOT_FOUND", "报价不存在", status_code=404)
    snapshot = json.loads(obj.snapshot_json)
    html = render_quote_html(snapshot, type)
    headers = {"Content-Disposition": f'inline; filename="quote-{quote_id}-{type}.html"'}
    if format != "html":
        headers["X-Export-Fallback"] = "html"
    return HTMLResponse(html, headers=headers)
