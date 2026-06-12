from decimal import Decimal

from app.models import (
    BOMItem,
    CostSetting,
    Machine,
    Material,
    Part,
    PrintFilament,
    PrintItem,
    Product,
)
from app.services.bom_validator import BOMCycleError
from app.services.cost_assembler import assemble_product_cost


def _setup_settings(db):
    db.add(
        CostSetting(
            id=1,
            electricity_price=Decimal("0.65"),
            scrap_rate=Decimal("0.05"),
            labor_rate=Decimal("30"),
            default_markup=Decimal("1.6"),
        )
    )
    db.flush()


def test_assemble_flat_product(db_session):
    db = db_session
    _setup_settings(db)
    m = Material(name="PLA", type="PLA", avg_price_per_g=Decimal("0.085"))
    db.add(m)
    mac = Machine(name="X1C", price=Decimal("7999"), life_hours=10000, power_w=350)
    db.add(mac)
    db.flush()
    pi = PrintItem(name="件", machine_id=mac.id, print_hours=Decimal("1"))
    db.add(pi)
    db.flush()
    db.add(PrintFilament(print_item_id=pi.id, material_id=m.id, grams=Decimal("200")))
    db.flush()
    part = Part(name="电源", avg_unit_price=Decimal("17.33"))
    db.add(part)
    db.flush()
    prod = Product(name="成品", markup_rate=Decimal("1.6"))
    db.add(prod)
    db.flush()
    db.add_all(
        [
            BOMItem(product_id=prod.id, kind="printitem", ref_id=pi.id, qty=Decimal("1")),
            BOMItem(product_id=prod.id, kind="part", ref_id=part.id, qty=Decimal("1")),
            BOMItem(product_id=prod.id, kind="postprocess", hours=Decimal("0.8")),
        ]
    )
    db.flush()

    detail, snapshots = assemble_product_cost(db, prod)
    # 打印件: 耗材200*0.085=17 + 机时1*(0.7999+0.2275)=1.0274→1.03 = 18.03
    assert detail["printitems_cost"] == Decimal("18.03")
    assert detail["parts_cost"] == Decimal("17.33")
    assert detail["postprocess_cost"] == Decimal("24.00")
    # subtotal=59.36; scrap5%=2.968→2.97; total=62.33; price 用未舍入 62.328*1.6=99.7248→99.72
    assert detail["subtotal"] == Decimal("59.36")
    assert detail["total_cost"] == Decimal("62.33")
    assert detail["customer_price"] == Decimal("99.72")
    assert len(snapshots) == 3


def test_assemble_with_subproduct(db_session):
    db = db_session
    _setup_settings(db)
    part = Part(name="件", avg_unit_price=Decimal("10"))
    db.add(part)
    db.flush()
    child = Product(name="子", markup_rate=Decimal("9"))
    db.add(child)
    db.flush()
    db.add(BOMItem(product_id=child.id, kind="part", ref_id=part.id, qty=Decimal("1")))
    db.flush()
    parent = Product(name="父", markup_rate=Decimal("2"))
    db.add(parent)
    db.flush()
    db.add(BOMItem(product_id=parent.id, kind="subproduct", ref_id=child.id, qty=Decimal("1")))
    db.flush()

    detail, _ = assemble_product_cost(db, parent)
    # 子产品 total: 零件10, scrap5% → subtotal10, scrap0.5, total10.5
    # 父: subproduct=10.5; subtotal10.5; scrap0.525; total11.025→11.03(明细);
    #   customer_price 用未舍入 total*2 = 22.05
    assert detail["subproduct_cost"] == Decimal("10.50")
    assert detail["customer_price"] == Decimal("22.05")


def test_assemble_detects_cycle(db_session):
    db = db_session
    _setup_settings(db)
    a = Product(name="A", markup_rate=Decimal("1.6"))
    db.add(a)
    db.flush()
    b = Product(name="B", markup_rate=Decimal("1.6"))
    db.add(b)
    db.flush()
    db.add(BOMItem(product_id=a.id, kind="subproduct", ref_id=b.id, qty=Decimal("1")))
    db.add(BOMItem(product_id=b.id, kind="subproduct", ref_id=a.id, qty=Decimal("1")))
    db.flush()
    try:
        assemble_product_cost(db, a)
        assert False, "应抛 BOMCycleError"
    except BOMCycleError:
        pass
