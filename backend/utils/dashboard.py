"""
Phase 4 — Interactive Dashboard.

Computes retail business KPIs and chart-ready analytics from the cleaned
dataset (falling back to raw), with optional filtering by region,
category, and date range. Every metric degrades gracefully to `None`
with an explanatory note when the underlying column wasn't detected,
rather than guessing or fabricating a number.
"""
import numpy as np
import pandas as pd

from utils.schema_hints import match_columns_to_fields

TOP_N = 10
LOW_STOCK_THRESHOLD = 10


def _clean(value):
    if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 2)
    return value


def _prepare(df: pd.DataFrame, field_matches: dict) -> pd.DataFrame:
    df = df.copy()
    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


def get_filter_options(df: pd.DataFrame, field_matches: dict) -> dict:
    df = _prepare(df, field_matches)
    options = {"regions": [], "categories": [], "date_min": None, "date_max": None}

    region_col = field_matches.get("region")
    if region_col and region_col in df.columns:
        options["regions"] = sorted(df[region_col].dropna().astype(str).unique().tolist())

    category_col = field_matches.get("category")
    if category_col and category_col in df.columns:
        options["categories"] = sorted(df[category_col].dropna().astype(str).unique().tolist())

    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        valid_dates = df[date_col].dropna()
        if not valid_dates.empty:
            options["date_min"] = valid_dates.min().strftime("%Y-%m-%d")
            options["date_max"] = valid_dates.max().strftime("%Y-%m-%d")

    return options


def apply_filters(df: pd.DataFrame, field_matches: dict, filters: dict) -> pd.DataFrame:
    df = _prepare(df, field_matches)

    region_col = field_matches.get("region")
    if filters.get("region") and region_col and region_col in df.columns:
        df = df[df[region_col].astype(str) == filters["region"]]

    category_col = field_matches.get("category")
    if filters.get("category") and category_col and category_col in df.columns:
        df = df[df[category_col].astype(str) == filters["category"]]

    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        if filters.get("date_from"):
            df = df[df[date_col] >= pd.to_datetime(filters["date_from"])]
        if filters.get("date_to"):
            df = df[df[date_col] <= pd.to_datetime(filters["date_to"])]

    return df


def _compute_kpis(df: pd.DataFrame, field_matches: dict) -> dict:
    kpis = {}

    revenue_col = field_matches.get("revenue")
    order_col = field_matches.get("order_id")
    customer_col = field_matches.get("customer")
    profit_col = field_matches.get("profit")
    date_col = field_matches.get("order_date")

    total_revenue = _clean(df[revenue_col].sum()) if revenue_col and revenue_col in df.columns else None
    total_orders = (
        int(df[order_col].nunique()) if order_col and order_col in df.columns else int(len(df))
    )
    total_customers = (
        int(df[customer_col].nunique()) if customer_col and customer_col in df.columns else None
    )

    kpis["total_revenue"] = total_revenue
    kpis["total_orders"] = total_orders
    kpis["total_customers"] = total_customers

    if profit_col and profit_col in df.columns and total_revenue:
        total_profit = df[profit_col].sum()
        kpis["profit_margin_percent"] = _clean(total_profit / total_revenue * 100) if total_revenue else None
    else:
        kpis["profit_margin_percent"] = None

    if total_revenue is not None and total_orders:
        kpis["average_order_value"] = _clean(total_revenue / total_orders)
    else:
        kpis["average_order_value"] = None

    kpis["monthly_growth_percent"] = None
    if revenue_col and date_col and date_col in df.columns and revenue_col in df.columns:
        monthly = (
            df.dropna(subset=[date_col])
            .set_index(date_col)
            .resample("ME")[revenue_col]
            .sum()
        )
        monthly = monthly[monthly.index.notna()]
        if len(monthly) >= 2:
            prev, curr = monthly.iloc[-2], monthly.iloc[-1]
            if prev:
                kpis["monthly_growth_percent"] = _clean((curr - prev) / prev * 100)

    return kpis


def _revenue_trend(df: pd.DataFrame, field_matches: dict) -> dict | None:
    date_col = field_matches.get("order_date")
    revenue_col = field_matches.get("revenue")
    if not date_col or date_col not in df.columns:
        return None
    working = df.dropna(subset=[date_col]).copy()
    if working.empty:
        return None
    working["value"] = working[revenue_col] if revenue_col in working.columns else 1
    monthly = working.set_index(date_col).resample("ME")["value"].sum()
    return {
        "x": [d.strftime("%Y-%m") for d in monthly.index],
        "y": [_clean(v) for v in monthly.values],
    }


def _regional_sales(df: pd.DataFrame, field_matches: dict) -> dict | None:
    region_col = field_matches.get("region")
    revenue_col = field_matches.get("revenue")
    if not region_col or region_col not in df.columns:
        return None
    if revenue_col and revenue_col in df.columns:
        grouped = df.groupby(region_col)[revenue_col].sum().sort_values(ascending=False)
    else:
        grouped = df[region_col].value_counts()
    return {"labels": [str(i) for i in grouped.index], "values": [_clean(v) for v in grouped.values]}


def _product_performance(df: pd.DataFrame, field_matches: dict, ascending=False) -> list[dict] | None:
    product_col = field_matches.get("product")
    revenue_col = field_matches.get("revenue")
    quantity_col = field_matches.get("quantity")
    if not product_col or product_col not in df.columns:
        return None

    agg = {}
    if revenue_col and revenue_col in df.columns:
        agg["revenue"] = (revenue_col, "sum")
    if quantity_col and quantity_col in df.columns:
        agg["units_sold"] = (quantity_col, "sum")
    if not agg:
        agg["orders"] = (product_col, "count")

    grouped = df.groupby(product_col).agg(**agg).reset_index()
    sort_col = "revenue" if "revenue" in grouped.columns else grouped.columns[1]
    grouped = grouped.sort_values(sort_col, ascending=ascending).head(TOP_N)

    records = []
    for row in grouped.to_dict(orient="records"):
        clean_row = {}
        for k, v in row.items():
            clean_row[k] = str(v) if k == product_col else _clean(v)
        records.append(clean_row)
    return records


def _customer_distribution(df: pd.DataFrame, field_matches: dict) -> dict | None:
    customer_col = field_matches.get("customer")
    revenue_col = field_matches.get("revenue")
    if not customer_col or customer_col not in df.columns:
        return None
    if revenue_col and revenue_col in df.columns:
        grouped = df.groupby(customer_col)[revenue_col].sum().sort_values(ascending=False).head(TOP_N)
    else:
        grouped = df[customer_col].value_counts().head(TOP_N)
    return {"labels": [str(i) for i in grouped.index], "values": [_clean(v) for v in grouped.values]}


def _revenue_vs_profit(df: pd.DataFrame, field_matches: dict) -> dict | None:
    date_col = field_matches.get("order_date")
    revenue_col = field_matches.get("revenue")
    profit_col = field_matches.get("profit")
    if not (date_col and revenue_col and profit_col):
        return None
    if not all(c in df.columns for c in (date_col, revenue_col, profit_col)):
        return None
    working = df.dropna(subset=[date_col])
    if working.empty:
        return None
    monthly = working.set_index(date_col).resample("ME")[[revenue_col, profit_col]].sum()
    return {
        "x": [d.strftime("%Y-%m") for d in monthly.index],
        "revenue": [_clean(v) for v in monthly[revenue_col].values],
        "profit": [_clean(v) for v in monthly[profit_col].values],
    }


def _inventory_status(df: pd.DataFrame, field_matches: dict) -> dict | None:
    stock_col = field_matches.get("stock")
    product_col = field_matches.get("product")
    if not stock_col or stock_col not in df.columns:
        return None

    if product_col and product_col in df.columns:
        latest_stock = df.groupby(product_col)[stock_col].last()
    else:
        latest_stock = df[stock_col]

    low_stock = latest_stock[latest_stock < LOW_STOCK_THRESHOLD]
    return {
        "total_units_in_stock": _clean(latest_stock.sum()),
        "low_stock_count": int(len(low_stock)),
        "low_stock_items": [
            {"name": str(i), "stock": _clean(v)} for i, v in low_stock.sort_values().items()
        ][:TOP_N],
    }


def build_dashboard(df: pd.DataFrame, filters: dict | None = None) -> dict:
    filters = filters or {}
    field_matches = match_columns_to_fields([str(c) for c in df.columns])

    filtered = apply_filters(df, field_matches, filters)
    unavailable_notes = []

    if not field_matches.get("revenue"):
        unavailable_notes.append("No revenue column detected — revenue-based KPIs and charts are unavailable.")
    if not field_matches.get("profit"):
        unavailable_notes.append("No profit column detected — profit margin and revenue-vs-profit are unavailable.")
    if not field_matches.get("order_date"):
        unavailable_notes.append("No order date column detected — trend and monthly growth are unavailable.")
    if not field_matches.get("stock"):
        unavailable_notes.append("No stock/inventory column detected — inventory status is unavailable.")

    return {
        "schema_match": field_matches,
        "applied_filters": filters,
        "row_count": int(len(filtered)),
        "kpis": _compute_kpis(filtered, field_matches),
        "analytics": {
            "revenue_trend": _revenue_trend(filtered, field_matches),
            "regional_sales": _regional_sales(filtered, field_matches),
            "top_selling_products": _product_performance(filtered, field_matches, ascending=False),
            "low_performing_products": _product_performance(filtered, field_matches, ascending=True),
            "customer_distribution": _customer_distribution(filtered, field_matches),
            "revenue_vs_profit": _revenue_vs_profit(filtered, field_matches),
            "inventory_status": _inventory_status(filtered, field_matches),
        },
        "unavailable_notes": unavailable_notes,
    }
