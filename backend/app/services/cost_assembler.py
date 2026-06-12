from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Machine, Material, PrintItem
from app.repositories import settings_repo
from app.responses import APIError
from app.services import costing


def assemble_print_item_cost(db: Session, print_item: PrintItem) -> dict[str, Decimal]:
    """从 DB 装配打印件成本所需数据并计算成本。缺机器时抛 COST_SOURCE_MISSING。"""
    machine = db.get(Machine, print_item.machine_id)
    if machine is None:
        raise APIError(
            "COST_SOURCE_MISSING", "打印件关联的机器不存在", status_code=400,
            details={"machine_id": print_item.machine_id},
        )

    filament_rows: list[tuple[Decimal, Decimal]] = []
    for f in print_item.filaments:
        material = db.get(Material, f.material_id)
        price = material.avg_price_per_g if material else Decimal("0")
        filament_rows.append((f.grams, price))

    setting = settings_repo.get_or_create(db)
    return costing.calc_print_item_cost(
        filaments=filament_rows,
        print_hours=print_item.print_hours,
        machine_price=machine.price,
        machine_life_hours=machine.life_hours,
        machine_power_w=machine.power_w,
        electricity_price=setting.electricity_price,
    )
