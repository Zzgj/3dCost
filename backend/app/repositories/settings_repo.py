from sqlalchemy.orm import Session

from app.models import CostSetting


def get_or_create(db: Session) -> CostSetting:
    obj = db.get(CostSetting, 1)
    if obj is None:
        obj = CostSetting(id=1)
        db.add(obj)
        db.flush()
    return obj


def update(db: Session, obj: CostSetting, **fields) -> CostSetting:
    for key, value in fields.items():
        setattr(obj, key, value)
    db.flush()
    return obj
