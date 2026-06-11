from decimal import ROUND_HALF_UP, Decimal

QUANT_AMOUNT = Decimal("0.0001")  # 金额内部保留 4 位


def weighted_avg_price(total_amount: Decimal, total_qty: Decimal) -> Decimal:
    """加权平均到手价 = 总金额（含运费） / 总数量。total_qty<=0 时返回 0。"""
    if total_qty is None or total_qty <= 0:
        return Decimal("0")
    return (total_amount / total_qty).quantize(QUANT_AMOUNT, rounding=ROUND_HALF_UP)


def material_total_grams(rows: list[tuple[int, int]]) -> Decimal:
    """rows: [(qty_rolls, grams_per_roll), ...] → 总克数。"""
    total = Decimal("0")
    for qty_rolls, grams_per_roll in rows:
        total += Decimal(qty_rolls) * Decimal(grams_per_roll)
    return total


def part_total_use_qty(rows: list[tuple[Decimal, Decimal]]) -> Decimal:
    """rows: [(qty, conversion_ratio), ...] → 总使用单位数量。"""
    total = Decimal("0")
    for qty, ratio in rows:
        total += Decimal(qty) * Decimal(ratio)
    return total
