"""
Phase 8 — Ask INSIGHT IQ: context assembly.

Ask INSIGHT IQ never sees the whole raw file — that would blow past
context limits on anything but a toy dataset, and it's not what makes
the answers good anyway. Instead it gets the same condensed, already
-computed numbers the rest of the app already trusts (dashboard KPIs,
insights, predictive results) plus a small sample of raw rows for
grounding on specific values and formatting.
"""
import pandas as pd


def _fmt_money(value):
    if value is None:
        return "not available"
    return f"₹{value:,.0f}"


def _fmt_pct(value):
    if value is None:
        return "not available"
    return f"{value}%"


def build_dataset_context(df: pd.DataFrame, field_matches: dict, dashboard_data: dict, insights_report, predictive_report, dataset_meta: dict) -> str:
    lines = []

    lines.append(f"Dataset file: {dataset_meta['filename']}")
    lines.append(f"Rows: {dataset_meta['row_count']:,} ({dataset_meta['source_stage']} data)")
    lines.append(f"Columns: {', '.join(str(c) for c in df.columns)}")

    detected = {k: v for k, v in field_matches.items() if v}
    if detected:
        lines.append("Detected retail fields: " + ", ".join(f"{k}={v}" for k, v in detected.items()))

    kpis = dashboard_data.get("kpis", {})
    lines.append("\nKey metrics:")
    lines.append(f"- Total revenue: {_fmt_money(kpis.get('total_revenue'))}")
    lines.append(f"- Total orders: {kpis.get('total_orders')}")
    lines.append(f"- Total customers: {kpis.get('total_customers')}")
    lines.append(f"- Profit margin: {_fmt_pct(kpis.get('profit_margin_percent'))}")
    lines.append(f"- Average order value: {_fmt_money(kpis.get('average_order_value'))}")
    lines.append(f"- Month-over-month revenue growth: {_fmt_pct(kpis.get('monthly_growth_percent'))}")

    analytics = dashboard_data.get("analytics", {})
    regional = analytics.get("regional_sales")
    if regional:
        pairs = ", ".join(f"{l}: {_fmt_money(v)}" for l, v in zip(regional["labels"], regional["values"]))
        lines.append(f"\nRevenue by region: {pairs}")

    top_products = analytics.get("top_selling_products")
    if top_products:
        keys = list(top_products[0].keys())
        name_key = keys[0]
        formatted = "; ".join(
            f"{p[name_key]} ({', '.join(f'{k}: {p[k]}' for k in keys[1:])})" for p in top_products[:5]
        )
        lines.append(f"Top selling products: {formatted}")

    low_products = analytics.get("low_performing_products")
    if low_products:
        keys = list(low_products[0].keys())
        name_key = keys[0]
        formatted = "; ".join(
            f"{p[name_key]} ({', '.join(f'{k}: {p[k]}' for k in keys[1:])})" for p in low_products[:5]
        )
        lines.append(f"Lowest performing products: {formatted}")

    customers = analytics.get("customer_distribution")
    if customers:
        pairs = ", ".join(f"{l}: {_fmt_money(v)}" for l, v in zip(customers["labels"], customers["values"]))
        lines.append(f"Top customers by revenue: {pairs}")

    inventory = analytics.get("inventory_status")
    if inventory:
        lines.append(
            f"Inventory: {inventory['total_units_in_stock']} total units in stock, "
            f"{inventory['low_stock_count']} product(s) low on stock."
        )

    if insights_report and insights_report.get("insights"):
        lines.append("\nBusiness insights already generated:")
        for i in insights_report["insights"]:
            lines.append(f"- [{i['category']}] {i['message']}")

    if predictive_report:
        sp = predictive_report.get("sales_prediction", {})
        if sp.get("available"):
            lines.append(f"\nSales prediction model: R² {sp['metrics']['r2']}, trained on {sp['rows_used']} rows.")

        rf = predictive_report.get("revenue_forecast", {})
        if rf.get("available"):
            forecast_pairs = ", ".join(f"{x}: {_fmt_money(y)}" for x, y in zip(rf["forecast"]["x"], rf["forecast"]["y"]))
            lines.append(f"Revenue forecast (next {len(rf['forecast']['x'])} months): {forecast_pairs}")

        seg = predictive_report.get("customer_segmentation", {})
        if seg.get("available"):
            seg_desc = "; ".join(
                f"{s['label']} ({s['size']} customers, avg revenue {_fmt_money(s['avg_total_revenue'])})"
                for s in seg["segments"]
            )
            lines.append(f"Customer segments: {seg_desc}")

        churn = predictive_report.get("churn_prediction", {})
        if churn.get("available"):
            at_risk_names = ", ".join(c["customer"] for c in churn["at_risk_customers"][:5])
            lines.append(
                f"Churn model: estimated {churn['churn_rate_percent']}% churn rate. "
                f"Highest-risk customers: {at_risk_names}."
            )

    sample = df.head(5)
    lines.append("\nSample rows (first 5, for reference only — do not assume these represent every row):")
    lines.append(sample.to_csv(index=False))

    unavailable = dashboard_data.get("unavailable_notes") or []
    if unavailable:
        lines.append("Known gaps in this dataset: " + " ".join(unavailable))

    return "\n".join(lines)


SYSTEM_PROMPT_TEMPLATE = """You are Ask INSIGHT IQ, a business intelligence assistant embedded in the \
INSIGHT IQ retail analytics platform. A user is asking about a specific dataset they uploaded.

Answer ONLY using the dataset context provided below. It contains the actual computed metrics, \
insights, and predictive results for this dataset, plus a small sample of raw rows.

Rules:
- If the answer is directly supported by the context, answer clearly and cite the specific number.
- If something is not covered by the context (e.g. a metric that needs a column this dataset doesn't \
have, or an analysis that hasn't been run yet), say so plainly and, if relevant, suggest which \
INSIGHT IQ feature (Predictive Analytics, Business Insights, Dashboard filters) would answer it.
- Never invent numbers that aren't in the context.
- Keep answers concise and in plain business language — the user is a business owner, not a data scientist.

--- DATASET CONTEXT ---
{context}
--- END CONTEXT ---
"""


def build_system_prompt(context_text: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(context=context_text)
