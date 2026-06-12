from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import print_item_repo
from app.responses import APIError, ok, ok_list
from app.schemas import PrintItemCreate, PrintItemOut, PrintItemUpdate
from app.services import cost_assembler

router = APIRouter(prefix="/api/print-items", tags=["print-items"])


def _get_or_404(db: Session, print_item_id: int):
    obj = print_item_repo.get(db, print_item_id)
    if obj is None or not obj.is_active:
        raise APIError("NOT_FOUND", "打印件不存在", status_code=404)
    return obj


def _serialize(db: Session, obj) -> dict:
    cost = cost_assembler.assemble_print_item_cost(db, obj)
    data = PrintItemOut.model_validate(obj).model_dump(mode="json")
    data["cost"] = {k: str(v) for k, v in cost.items()}
    return data


def _serialize_safe(db: Session, obj) -> dict:
    """列表用：单件成本装配失败（如机器缺失）时降级，cost 置空并附 warning，
    不让整页列表请求失败。"""
    data = PrintItemOut.model_validate(obj).model_dump(mode="json")
    try:
        cost = cost_assembler.assemble_print_item_cost(db, obj)
        data["cost"] = {k: str(v) for k, v in cost.items()}
    except APIError as exc:
        data["cost"] = None
        data["cost_error"] = exc.code
    return data


@router.post("")
def create_print_item(payload: PrintItemCreate, db: Session = Depends(get_db)):
    fields = payload.model_dump(exclude={"filaments"})
    filaments = [f.model_dump() for f in payload.filaments]
    obj = print_item_repo.create(db, filaments=filaments, **fields)
    # 先装配成本（校验机器存在），失败则回滚，避免落库脏数据
    try:
        data = _serialize(db, obj)
    except APIError:
        db.rollback()
        raise
    db.commit()
    return ok(data)


@router.get("")
def list_print_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, total = print_item_repo.list_active(db, page, page_size)
    data = [_serialize_safe(db, r) for r in rows]
    return ok_list(data, page, page_size, total)


@router.get("/{print_item_id}")
def get_print_item(print_item_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, print_item_id)
    return ok(_serialize(db, obj))


@router.patch("/{print_item_id}")
def update_print_item(print_item_id: int, payload: PrintItemUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, print_item_id)
    fields = payload.model_dump(exclude_unset=True)
    filaments = fields.pop("filaments", None)
    print_item_repo.update(db, obj, filaments=filaments, **fields)
    # 先装配成本（校验机器存在），失败则回滚，避免提交无效引用
    try:
        data = _serialize(db, obj)
    except APIError:
        db.rollback()
        raise
    db.commit()
    return ok(data)


@router.delete("/{print_item_id}")
def delete_print_item(print_item_id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, print_item_id)
    print_item_repo.soft_delete(db, obj)
    db.commit()
    return ok({"deleted": print_item_id})
