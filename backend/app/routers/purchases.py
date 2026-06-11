from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import material_repo, part_repo, purchase_repo
from app.responses import APIError, ok
from app.schemas import PurchaseCreate, PurchaseOut, PurchaseResult
from app.services import inventory

router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@router.post("")
def create_purchase(payload: PurchaseCreate, db: Session = Depends(get_db)):
    if payload.target_kind == "material":
        if payload.qty_rolls is None or payload.grams_per_roll is None:
            raise APIError(
                "VALIDATION_ERROR", "耗材采购需提供 qty_rolls 与 grams_per_roll",
                status_code=400,
            )
        material = material_repo.get(db, payload.target_id)
        if material is None or not material.is_active:
            raise APIError("NOT_FOUND", "耗材不存在", status_code=404)
        result = inventory.record_material_purchase(
            db, material,
            qty_rolls=payload.qty_rolls, grams_per_roll=payload.grams_per_roll,
            goods_amount=payload.goods_amount, shipping_fee=payload.shipping_fee,
            supplier_id=payload.supplier_id, purchase_url=payload.purchase_url,
            purchased_at=payload.purchased_at,
        )
    else:  # part
        if payload.qty is None:
            raise APIError("VALIDATION_ERROR", "零件采购需提供 qty", status_code=400)
        part = part_repo.get(db, payload.target_id)
        if part is None or not part.is_active:
            raise APIError("NOT_FOUND", "零件不存在", status_code=404)
        result = inventory.record_part_purchase(
            db, part,
            qty=payload.qty,
            goods_amount=payload.goods_amount, shipping_fee=payload.shipping_fee,
            supplier_id=payload.supplier_id, purchase_url=payload.purchase_url,
            purchased_at=payload.purchased_at,
        )
    # 取最新一条采购用于响应
    rows = purchase_repo.list_for_target(db, payload.target_kind, payload.target_id)
    latest = rows[-1]
    db.commit()
    db.refresh(latest)
    out = PurchaseResult(
        purchase=PurchaseOut.model_validate(latest),
        updated_avg_price=result["updated_avg_price"],
        total_stock=result["total_stock"],
    )
    return ok(out.model_dump(mode="json"))


@router.get("")
def list_purchases(
    target_kind: str = Query(pattern="^(material|part)$"),
    target_id: int = Query(...),
    db: Session = Depends(get_db),
):
    rows = purchase_repo.list_for_target(db, target_kind, target_id)
    data = [PurchaseOut.model_validate(r).model_dump(mode="json") for r in rows]
    return ok(data)
