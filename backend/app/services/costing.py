from decimal import ROUND_HALF_UP, Decimal

QUANT_2 = Decimal("0.01")


def _r(v: Decimal) -> Decimal:
    return v.quantize(QUANT_2, rounding=ROUND_HALF_UP)


def calc_print_item_cost(
    filaments: list[tuple[Decimal, Decimal]],
    print_hours: Decimal,
    machine_price: Decimal,
    machine_life_hours: int,
    machine_power_w: int,
    electricity_price: Decimal,
) -> dict[str, Decimal]:
    """打印件成本 = 耗材成本(多色分项求和) + 机时成本(折旧+电费)。

    filaments: [(grams, price_per_g), ...]
    返回 {material_cost, machine_cost, total}，各项四舍五入到 2 位。
    """
    material_cost = sum(
        (grams * price_per_g for grams, price_per_g in filaments), Decimal("0")
    )
    depreciation_per_h = machine_price / Decimal(machine_life_hours)
    electricity_per_h = (Decimal(machine_power_w) / Decimal("1000")) * electricity_price
    machine_cost = print_hours * (depreciation_per_h + electricity_per_h)
    material_cost = _r(material_cost)
    machine_cost = _r(machine_cost)
    return {
        "material_cost": material_cost,
        "machine_cost": machine_cost,
        "total": _r(material_cost + machine_cost),
    }


def calc_product_cost(
    bom_items: list[dict],
    markup_rate: Decimal,
    labor_rate: Decimal,
    scrap_rate: Decimal,
) -> dict[str, Decimal]:
    """产品总成本（扁平计算，子产品 total 已由外层解析好作为 unit_price 传入）。

    bom_items: [{"kind": "printitem"|"part"|"postprocess"|"subproduct", "unit_price"?: Decimal, "qty"?: Decimal, "hours"?: Decimal}, ...]
    返回各项四舍五入到 2 位。
    """
    printitems_cost = Decimal("0")
    parts_cost = Decimal("0")
    postprocess_cost = Decimal("0")
    subproduct_cost = Decimal("0")

    for item in bom_items:
        kind = item["kind"]
        if kind == "printitem":
            printitems_cost += item["unit_price"] * item.get("qty", Decimal("1"))
        elif kind == "part":
            parts_cost += item["unit_price"] * item.get("qty", Decimal("1"))
        elif kind == "postprocess":
            postprocess_cost += item.get("hours", Decimal("0")) * labor_rate
        elif kind == "subproduct":
            subproduct_cost += item["unit_price"] * item.get("qty", Decimal("1"))

    subtotal = printitems_cost + parts_cost + postprocess_cost + subproduct_cost
    scrap_cost = subtotal * scrap_rate
    total_cost = subtotal + scrap_cost
    r_subtotal = _r(subtotal)
    r_scrap = _r(scrap_cost)
    r_total = _r(total_cost)
    customer_price = r_total * markup_rate

    return {
        "printitems_cost": _r(printitems_cost),
        "parts_cost": _r(parts_cost),
        "postprocess_cost": _r(postprocess_cost),
        "subproduct_cost": _r(subproduct_cost),
        "subtotal": r_subtotal,
        "scrap_cost": r_scrap,
        "total_cost": r_total,
        "customer_price": _r(customer_price),
    }
