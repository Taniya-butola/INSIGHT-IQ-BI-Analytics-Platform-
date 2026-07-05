"""
Phase 6 — Business Insights.

Turns the same aggregations already used by the dashboard and predictive
engines into short, plain-language sentences a business owner can read
without knowing what a correlation matrix is. Each generator returns
`None` (recorded as an "unavailable" note) when the dataset doesn't have
what it needs, rather than writing a sentence around a guessed number.
"""
import numpy as np
import pandas as pd

from utils.schema_hints import match_columns_to_fields

LOW_STOCK_THRESHOLD = 10
MIN_ROWS_FOR_TREND = 2


def _clean(value):
    if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 2)
    return value


def _money(value) -> str:
    if value is None:
        return "—"
    return f"₹{value:,.0f}"


def _prepare(df: pd.DataFrame, field_matches: dict) -> pd.DataFrame:
    df = df.copy()
    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


def _insight(category, title, message, tone, metric=None):
    return {"category": category, "title": title, "message": message, "tone": tone, "metric": metric}


# ---------------------------------------------------------------------------
# Individual insight generators — each returns an insight dict or None
# ---------------------------------------------------------------------------


def revenue_trend(df, field_matches):
    date_col, revenue_col = field_matches.get("order_date"), field_matches.get("revenue")
    if not date_col or not revenue_col or date_col not in df.columns or revenue_col not in df.columns:
        return None, "No order date or revenue column detected."

    monthly = df.dropna(subset=[date_col]).set_index(date_col).resample("ME")[revenue_col].sum()
    monthly = monthly[monthly.index.notna()]
    if len(monthly) < MIN_ROWS_FOR_TREND:
        return None, "Not enough months of order history to describe a trend."

    prev, curr = monthly.iloc[-2], monthly.iloc[-1]
    change_pct = ((curr - prev) / prev * 100) if prev else None
    last_month_label = monthly.index[-1].strftime("%B %Y")

    if change_pct is None:
        return None, "Prior month had zero revenue — growth rate isn't meaningful."

    direction = "grew" if change_pct >= 0 else "fell"
    tone = "positive" if change_pct >= 0 else "warning"
    message = (
        f"Revenue {direction} {abs(change_pct):.1f}% in {last_month_label}, moving from "
        f"{_money(prev)} to {_money(curr)} compared to the previous month."
    )
    return _insight("Revenue Trends", f"Revenue {direction} month-over-month", message, tone, _clean(change_pct)), None


def best_selling_products(df, field_matches):
    product_col, revenue_col = field_matches.get("product"), field_matches.get("revenue")
    if not product_col or product_col not in df.columns:
        return None, "No product column detected."
    if not revenue_col or revenue_col not in df.columns:
        return None, "No revenue column detected."

    grouped = df.groupby(product_col)[revenue_col].sum().sort_values(ascending=False)
    if grouped.empty:
        return None, "No product sales to summarize."

    top_product, top_revenue = grouped.index[0], grouped.iloc[0]
    total_revenue = grouped.sum()
    share = (top_revenue / total_revenue * 100) if total_revenue else 0

    message = (
        f"{top_product} was your best-selling product, generating {_money(top_revenue)} — "
        f"{share:.1f}% of total revenue."
    )
    return _insight("Product Performance", "Best-selling product", message, "positive", _clean(share)), None


def worst_performing_products(df, field_matches):
    product_col, revenue_col = field_matches.get("product"), field_matches.get("revenue")
    if not product_col or product_col not in df.columns:
        return None, "No product column detected."
    if not revenue_col or revenue_col not in df.columns:
        return None, "No revenue column detected."

    grouped = df.groupby(product_col)[revenue_col].agg(["sum", "count"])
    grouped = grouped[grouped["count"] >= 1].sort_values("sum")
    if len(grouped) < 2:
        return None, "Not enough distinct products to identify a laggard."

    worst_product = grouped.index[0]
    worst_revenue, worst_orders = grouped.iloc[0]["sum"], int(grouped.iloc[0]["count"])

    message = (
        f"{worst_product} was your lowest-performing product, generating only "
        f"{_money(worst_revenue)} across {worst_orders} order(s) — consider a promotion, bundling, "
        f"or reviewing its pricing."
    )
    return _insight("Product Performance", "Lowest-performing product", message, "warning"), None


def regional_performance(df, field_matches):
    region_col, revenue_col = field_matches.get("region"), field_matches.get("revenue")
    if not region_col or region_col not in df.columns:
        return None, "No region column detected."
    if not revenue_col or revenue_col not in df.columns:
        return None, "No revenue column detected."

    grouped = df.groupby(region_col)[revenue_col].sum().sort_values(ascending=False)
    if len(grouped) < 2:
        return None, "Not enough distinct regions to compare."

    total = grouped.sum()
    top_region, top_revenue = grouped.index[0], grouped.iloc[0]
    bottom_region, bottom_revenue = grouped.index[-1], grouped.iloc[-1]
    top_share = (top_revenue / total * 100) if total else 0

    message = (
        f"{top_region} led all regions with {_money(top_revenue)} in revenue ({top_share:.1f}% of "
        f"the total), while {bottom_region} lagged behind at {_money(bottom_revenue)}."
    )
    return _insight("Regional Performance", "Regional leader and laggard", message, "neutral"), None


def customer_purchasing_behavior(df, field_matches):
    customer_col = field_matches.get("customer")
    revenue_col = field_matches.get("revenue")
    order_col = field_matches.get("order_id")
    if not customer_col or customer_col not in df.columns:
        return None, "No customer column detected."

    if order_col and order_col in df.columns:
        orders_per_customer = df.groupby(customer_col)[order_col].nunique()
    else:
        orders_per_customer = df.groupby(customer_col).size()

    repeat_customers = (orders_per_customer > 1).sum()
    total_customers = len(orders_per_customer)
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers else 0

    avg_order_value_text = ""
    if revenue_col and revenue_col in df.columns and order_col and order_col in df.columns:
        aov = df[revenue_col].sum() / df[order_col].nunique()
        avg_order_value_text = f" Orders averaged {_money(aov)} in value."

    message = (
        f"{repeat_rate:.1f}% of your {total_customers} customers placed more than one order."
        f"{avg_order_value_text}"
    )
    tone = "positive" if repeat_rate >= 30 else "neutral"
    return _insight("Customer Behavior", "Repeat purchase rate", message, tone, _clean(repeat_rate)), None


def high_value_customers(df, field_matches):
    customer_col, revenue_col = field_matches.get("customer"), field_matches.get("revenue")
    if not customer_col or customer_col not in df.columns:
        return None, "No customer column detected."
    if not revenue_col or revenue_col not in df.columns:
        return None, "No revenue column detected."

    grouped = df.groupby(customer_col)[revenue_col].sum().sort_values(ascending=False)
    if len(grouped) < 3:
        return None, "Not enough distinct customers to describe concentration."

    total = grouped.sum()
    top_n = max(1, round(len(grouped) * 0.2))
    top_share = (grouped.head(top_n).sum() / total * 100) if total else 0
    top_customer, top_customer_revenue = grouped.index[0], grouped.iloc[0]

    message = (
        f"Your top customer, {top_customer}, has contributed {_money(top_customer_revenue)}. "
        f"Your top {top_n} customer(s) (top 20%) account for {top_share:.1f}% of total revenue — "
        f"keeping them engaged matters more than growing the customer count alone."
    )
    return _insight("High-Value Customers", "Revenue concentration", message, "positive", _clean(top_share)), None


def growth_opportunities(df, field_matches):
    category_col = field_matches.get("category") or field_matches.get("region")
    revenue_col = field_matches.get("revenue")
    order_col = field_matches.get("order_id")
    if not category_col or category_col not in df.columns:
        return None, "No category or region column detected."
    if not revenue_col or revenue_col not in df.columns:
        return None, "No revenue column detected."

    if order_col and order_col in df.columns:
        grouped = df.groupby(category_col).agg(revenue=(revenue_col, "sum"), orders=(order_col, "nunique"))
    else:
        grouped = df.groupby(category_col).agg(revenue=(revenue_col, "sum"), orders=(revenue_col, "count"))

    if len(grouped) < 2:
        return None, "Not enough distinct groups to spot an opportunity."

    grouped["avg_order_value"] = grouped["revenue"] / grouped["orders"].replace(0, np.nan)
    median_orders = grouped["orders"].median()
    candidates = grouped[grouped["orders"] <= median_orders].sort_values("avg_order_value", ascending=False)
    if candidates.empty:
        return None, "No clear high-value, low-volume group stood out."

    best = candidates.iloc[0]
    label = candidates.index[0]

    message = (
        f"{label} has a high average order value ({_money(best['avg_order_value'])}) but relatively "
        f"few orders ({int(best['orders'])}) compared to other groups — targeted promotion here could "
        f"convert its high per-order value into more volume."
    )
    return _insight("Growth Opportunities", "Under-promoted high-value segment", message, "opportunity"), None


def inventory_alerts(df, field_matches):
    stock_col, product_col = field_matches.get("stock"), field_matches.get("product")
    if not stock_col or stock_col not in df.columns:
        return None, "No stock/inventory column detected."

    if product_col and product_col in df.columns:
        latest_stock = df.groupby(product_col)[stock_col].last()
    else:
        latest_stock = df[stock_col]

    low_stock = latest_stock[latest_stock < LOW_STOCK_THRESHOLD].sort_values()
    if low_stock.empty:
        return _insight(
            "Inventory Alerts", "Stock levels look healthy",
            f"No products are below the {LOW_STOCK_THRESHOLD}-unit low-stock threshold right now.",
            "positive",
        ), None

    names = ", ".join(str(i) for i in low_stock.head(5).index)
    message = (
        f"{len(low_stock)} product(s) are running low on stock (fewer than {LOW_STOCK_THRESHOLD} "
        f"units), including {names}. Consider restocking soon to avoid missed sales."
    )
    return _insight("Inventory Alerts", f"{len(low_stock)} product(s) low on stock", message, "warning"), None


def seasonal_sales_trends(df, field_matches):
    date_col, revenue_col = field_matches.get("order_date"), field_matches.get("revenue")
    if not date_col or date_col not in df.columns:
        return None, "No order date column detected."

    working = df.dropna(subset=[date_col]).copy()
    working["value"] = df[revenue_col] if revenue_col and revenue_col in df.columns else 1
    monthly = working.set_index(date_col).resample("ME")["value"].sum()
    if len(monthly) < 3:
        return None, "Need at least 3 months of history to describe a seasonal pattern."

    peak_month, peak_value = monthly.idxmax().strftime("%B %Y"), monthly.max()
    low_month, low_value = monthly.idxmin().strftime("%B %Y"), monthly.min()

    unit = _money(peak_value) if revenue_col else f"{int(peak_value)} orders"
    unit_low = _money(low_value) if revenue_col else f"{int(low_value)} orders"

    message = (
        f"Sales peaked in {peak_month} ({unit}) and were lowest in {low_month} ({unit_low}). "
        f"If this pattern repeats, plan inventory and staffing around the busier period."
    )
    return _insight("Seasonal Trends", "Peak and low sales periods", message, "neutral"), None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

_GENERATORS = [
    revenue_trend,
    best_selling_products,
    worst_performing_products,
    regional_performance,
    customer_purchasing_behavior,
    high_value_customers,
    growth_opportunities,
    inventory_alerts,
    seasonal_sales_trends,
]


def generate_insights(df: pd.DataFrame) -> dict:
    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    df = _prepare(df, field_matches)

    insights = []
    unavailable_notes = []

    for generator in _GENERATORS:
        insight, reason = generator(df, field_matches)
        if insight:
            insights.append(insight)
        elif reason:
            unavailable_notes.append(f"{generator.__name__.replace('_', ' ').title()}: {reason}")

    return {
        "schema_match": field_matches,
        "insights": insights,
        "unavailable_notes": unavailable_notes,
    }
