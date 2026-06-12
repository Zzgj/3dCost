from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import CostSetting


def get_or_create(db: Session) -> CostSetting:
    obj = db.get(CostSetting, 1)
    if obj is None:
        obj = CostSetting(id=1)
        db.add(obj)
        db.flush()
    return obj


def get_or_default(db: Session) -> CostSetting:
    """只读获取成本参数。不存在时返回带默认值的临时实例，不写库。

    用于成本计算等只读路径，避免在 GET 请求中产生写副作用。
    临时实例需显式带默认值（列默认值仅在 flush 时应用）。
    """
    obj = db.get(CostSetting, 1)
    if obj is not None:
        return obj
    return CostSetting(
        id=1,
        electricity_price=Decimal("0.65"),
        default_machine_id=None,
        scrap_rate=Decimal("0.05"),
        labor_rate=Decimal("30"),
        default_markup=Decimal("1.6"),
    )


def update(db: Session, obj: CostSetting, **fields) -> CostSetting:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj
