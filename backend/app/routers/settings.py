from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import settings_repo
from app.responses import ok
from app.schemas import CostSettingOut, CostSettingUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/cost")
def get_cost_settings(db: Session = Depends(get_db)):
    obj = settings_repo.get_or_create(db)
    db.commit()
    db.refresh(obj)
    return ok(CostSettingOut.model_validate(obj).model_dump(mode="json"))


@router.patch("/cost")
def update_cost_settings(payload: CostSettingUpdate, db: Session = Depends(get_db)):
    obj = settings_repo.get_or_create(db)
    settings_repo.update(db, obj, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(obj)
    return ok(CostSettingOut.model_validate(obj).model_dump(mode="json"))
