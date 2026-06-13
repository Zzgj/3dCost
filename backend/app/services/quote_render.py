import html
from datetime import datetime


def render_quote_html(snapshot: dict, view_type: str) -> str:
    """Render a printable quote snapshot as standalone HTML."""
    product = snapshot["product"]
    cost = snapshot["cost_detail"]
    bom_items = snapshot.get("bom_items", [])
    show_internal = view_type == "internal"
    title = "内部报价单" if show_internal else "客户报价单"
    generated_at = snapshot.get("created_at", datetime.utcnow().isoformat())

    def money(value: object) -> str:
        return f"{value} 元"

    rows = ""
    if show_internal:
        for item in bom_items:
            rows += (
                "<tr>"
                f"<td>{html.escape(str(item.get('kind_label', item.get('kind', ''))))}</td>"
                f"<td>{html.escape(str(item.get('ref_name') or '-'))}</td>"
                f"<td>{html.escape(str(item.get('qty') or item.get('hours') or '-'))}</td>"
                f"<td>{money(item.get('unit_price'))}</td>"
                f"<td>{money(item.get('subtotal'))}</td>"
                "</tr>"
            )

    bom_table = ""
    if show_internal:
        bom_table = f"""
        <h2>BOM 明细</h2>
        <table>
          <thead><tr><th>类型</th><th>项目</th><th>数量/工时</th><th>单价</th><th>小计</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """

    internal_detail = ""
    if show_internal:
        internal_detail = f"""
        <h2>成本明细</h2>
        <div class="grid">
          <div><span>打印件</span><strong>{money(cost["printitems_cost"])}</strong></div>
          <div><span>零件</span><strong>{money(cost["parts_cost"])}</strong></div>
          <div><span>后处理</span><strong>{money(cost["postprocess_cost"])}</strong></div>
          <div><span>子产品</span><strong>{money(cost["subproduct_cost"])}</strong></div>
          <div><span>小计</span><strong>{money(cost["subtotal"])}</strong></div>
          <div><span>废品成本</span><strong>{money(cost["scrap_cost"])}</strong></div>
        </div>
        """

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)} - {html.escape(product["name"])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 40px; color: #1f2937; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin-top: 28px; font-size: 18px; }}
    .muted {{ color: #6b7280; }}
    .summary {{ margin-top: 24px; padding: 20px; border: 1px solid #d1d5db; border-radius: 8px; }}
    .price {{ font-size: 32px; color: #0f766e; margin-top: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .grid div {{ border: 1px solid #e5e7eb; padding: 12px; border-radius: 6px; }}
    .grid span {{ display: block; color: #6b7280; font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; text-align: left; padding: 10px 8px; }}
    th {{ background: #f9fafb; }}
    @media print {{ body {{ margin: 18mm; }} }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <div class="muted">生成时间：{html.escape(generated_at[:19].replace("T", " "))}</div>
  <div class="summary">
    <div class="muted">产品</div>
    <h2>{html.escape(product["name"])}</h2>
    <div class="muted">模式：{html.escape(product["mode"])}</div>
    <div class="price">{money(cost["customer_price"])}</div>
  </div>
  {internal_detail}
  {bom_table}
</body>
</html>
"""
