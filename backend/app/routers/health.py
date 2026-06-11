from fastapi import APIRouter

from app.config import settings
from app.responses import ok

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return ok({"status": "ok"})


@router.get("/meta")
def meta():
    return ok(
        {
            "version": settings.app_version,
            "enums": {
                "material_types": ["PLA", "PETG", "ABS", "TPU", "ASA"],
                "part_categories": ["电源", "电路板", "轴承", "螺丝", "胶水", "其他"],
                "bom_item_kinds": ["printitem", "part", "postprocess", "subproduct"],
                "product_modes": ["estimate", "actual"],
                "product_statuses": ["draft", "completed"],
            },
            "defaults": {
                "electricity_price": 0.65,
                "scrap_rate": 0.05,
                "labor_rate": 30,
                "default_markup": 1.6,
            },
        }
    )
