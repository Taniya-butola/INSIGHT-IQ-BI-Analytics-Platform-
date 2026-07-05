"""
Phase 3 — Exploratory Data Analysis.

Runs on the cleaned dataset when available (falls back to raw). Produces
a dataset summary, descriptive statistics, a correlation matrix, a
missing-value report, per-feature distributions, and pre-aggregated data
for five chart types (bar, line, pie, histogram, scatter) so the frontend
can render them without doing any data crunching of its own.
"""
import numpy as np
import pandas as pd

from utils.schema_hints import match_columns_to_fields

MAX_CORRELATION_COLUMNS = 10
HISTOGRAM_BINS = 10
TOP_N_CATEGORIES = 8
MAX_SCATTER_POINTS = 500


def _clean_for_json(value):
    if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 4)
    return value


def _numeric_categorical_columns(df: pd.DataFrame):
    numeric_cols = []
    date_cols = []
    categorical_cols = []

    for c in df.columns:
        series = df[c]
        if pd.api.types.is_datetime64_any_dtype(series):
            date_cols.append(c)
            continue

        if pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(c)
            continue

        non_null = series.dropna()
        if non_null.empty:
            continue
        if non_null.nunique() <= max(25, len(non_null) * 0.1):
            categorical_cols.append(c)

    return numeric_cols, categorical_cols, date_cols


def _dataset_summary(df: pd.DataFrame, numeric_cols, categorical_cols, date_cols) -> dict:
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
    }


def _descriptive_statistics(df: pd.DataFrame, numeric_cols) -> dict:
    stats = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        try:
            numeric_series = pd.to_numeric(series, errors="coerce")
            numeric_series = numeric_series.dropna()
        except Exception:
            continue
        if numeric_series.empty:
            continue
        try:
            quantiles = {
                "p25": numeric_series.quantile(0.25),
                "median": numeric_series.median(),
                "p75": numeric_series.quantile(0.75),
            }
        except Exception:
            quantiles = {"p25": None, "median": None, "p75": None}
        stats[col] = {
            "count": int(numeric_series.count()),
            "mean": _clean_for_json(numeric_series.mean()),
            "std": _clean_for_json(numeric_series.std()),
            "min": _clean_for_json(numeric_series.min()),
            "p25": _clean_for_json(quantiles["p25"]),
            "median": _clean_for_json(quantiles["median"]),
            "p75": _clean_for_json(quantiles["p75"]),
            "max": _clean_for_json(numeric_series.max()),
        }
    return stats


def _missing_value_report(df: pd.DataFrame) -> list[dict]:
    total = len(df)
    report = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        report.append(
            {
                "column": str(col),
                "missing_count": missing,
                "missing_percentage": round(missing / total * 100, 2) if total else 0.0,
            }
        )
    return sorted(report, key=lambda r: r["missing_count"], reverse=True)


def _correlation_matrix(df: pd.DataFrame, numeric_cols) -> dict | None:
    cols = numeric_cols[:MAX_CORRELATION_COLUMNS]
    if len(cols) < 2:
        return None
    corr = df[cols].corr(numeric_only=True).round(3)
    matrix = [[_clean_for_json(v) for v in row] for row in corr.values]
    return {"columns": cols, "matrix": matrix}


def _feature_distributions(df: pd.DataFrame, numeric_cols, categorical_cols) -> dict:
    numeric_dist = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        try:
            counts, edges = np.histogram(series.astype(float), bins=HISTOGRAM_BINS)
        except Exception:
            continue
        numeric_dist[col] = {
            "bin_edges": [round(float(e), 2) for e in edges],
            "counts": [int(c) for c in counts],
        }

    categorical_dist = {}
    for col in categorical_cols:
        value_counts = df[col].value_counts(dropna=False).head(TOP_N_CATEGORIES)
        categorical_dist[col] = {
            "labels": [str(v) for v in value_counts.index],
            "counts": [int(v) for v in value_counts.values],
        }

    return {"numeric": numeric_dist, "categorical": categorical_dist}


def _bar_chart(df: pd.DataFrame, field_matches: dict) -> dict | None:
    group_col = field_matches.get("region") or field_matches.get("category")
    value_col = field_matches.get("revenue")
    if group_col and group_col in df.columns and value_col and value_col in df.columns:
        grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(12)
        return {
            "title": f"{value_col} by {group_col}",
            "x_label": group_col,
            "y_label": value_col,
            "categories": [str(i) for i in grouped.index],
            "values": [_clean_for_json(v) for v in grouped.values],
        }
    if group_col and group_col in df.columns:
        counts = df[group_col].value_counts().head(12)
        return {
            "title": f"Record count by {group_col}",
            "x_label": group_col,
            "y_label": "Count",
            "categories": [str(i) for i in counts.index],
            "values": [int(v) for v in counts.values],
        }
    return None


def _line_chart(df: pd.DataFrame, field_matches: dict) -> dict | None:
    date_col = field_matches.get("order_date")
    value_col = field_matches.get("revenue")
    if not date_col or date_col not in df.columns:
        return None
    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    if parsed_dates.notna().sum() == 0:
        return None
    working = pd.DataFrame({"date": parsed_dates})
    working["value"] = df[value_col] if value_col and value_col in df.columns else 1
    working = working.dropna(subset=["date"])
    daily = working.groupby(working["date"].dt.date)["value"].sum().sort_index()
    return {
        "title": f"{value_col or 'Orders'} over time",
        "x_label": "Date",
        "y_label": value_col or "Order count",
        "x": [str(d) for d in daily.index],
        "y": [_clean_for_json(v) for v in daily.values],
    }


def _pie_chart(df: pd.DataFrame, field_matches: dict) -> dict | None:
    col = field_matches.get("category") or field_matches.get("region")
    if not col or col not in df.columns:
        return None
    counts = df[col].value_counts().head(8)
    return {
        "title": f"Share by {col}",
        "labels": [str(i) for i in counts.index],
        "values": [int(v) for v in counts.values],
    }


def _histogram_chart(df: pd.DataFrame, field_matches: dict, numeric_cols) -> dict | None:
    col = field_matches.get("revenue") or (numeric_cols[0] if numeric_cols else None)
    if not col or col not in df.columns:
        return None
    series = df[col].dropna()
    if series.empty:
        return None
    counts, edges = np.histogram(series, bins=HISTOGRAM_BINS)
    labels = [f"{edges[i]:.0f}–{edges[i + 1]:.0f}" for i in range(len(edges) - 1)]
    return {
        "title": f"Distribution of {col}",
        "column": col,
        "labels": labels,
        "counts": [int(c) for c in counts],
    }


def _scatter_chart(df: pd.DataFrame, field_matches: dict, numeric_cols) -> dict | None:
    x_col = field_matches.get("quantity")
    y_col = field_matches.get("revenue")
    if not (x_col and y_col and x_col in df.columns and y_col in df.columns):
        if len(numeric_cols) >= 2:
            x_col, y_col = numeric_cols[0], numeric_cols[1]
        else:
            return None
    subset = df[[x_col, y_col]].dropna()
    if len(subset) > MAX_SCATTER_POINTS:
        subset = subset.sample(MAX_SCATTER_POINTS, random_state=42)
    numeric_subset = subset.apply(pd.to_numeric, errors="coerce")
    numeric_subset = numeric_subset.dropna()
    if numeric_subset.empty:
        return None
    return {
        "title": f"{y_col} vs {x_col}",
        "x_label": x_col,
        "y_label": y_col,
        "points": [
            {"x": _clean_for_json(row[x_col]), "y": _clean_for_json(row[y_col])}
            for _, row in subset.iterrows()
        ],
    }


def _to_jsonable(value):
    if value is None:
        return None
    if isinstance(value, (dict, list, tuple)):
        return value.__class__(
            (_to_jsonable(v) for v in value) if isinstance(value, (list, tuple)) else {k: _to_jsonable(v) for k, v in value.items()}
        )
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def generate_eda(df: pd.DataFrame) -> dict:
    df = df.copy()

    # opportunistically parse an order-date-like column to real datetimes
    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    numeric_cols, categorical_cols, date_cols = _numeric_categorical_columns(df)

    # order/invoice IDs are numeric but not a measure — keep them out of stats,
    # correlation, histograms, and scatter plots
    id_col = field_matches.get("order_id")
    if id_col in numeric_cols:
        numeric_cols = [c for c in numeric_cols if c != id_col]

    report = {
        "source_columns": [str(c) for c in df.columns],
        "schema_match": field_matches,
        "dataset_summary": _dataset_summary(df, numeric_cols, categorical_cols, date_cols),
        "descriptive_statistics": _descriptive_statistics(df, numeric_cols),
        "missing_value_report": _missing_value_report(df),
        "correlation_matrix": _correlation_matrix(df, numeric_cols),
        "feature_distributions": _feature_distributions(df, numeric_cols, categorical_cols),
        "charts": {
            "bar": _bar_chart(df, field_matches),
            "line": _line_chart(df, field_matches),
            "pie": _pie_chart(df, field_matches),
            "histogram": _histogram_chart(df, field_matches, numeric_cols),
            "scatter": _scatter_chart(df, field_matches, numeric_cols),
        },
    }
    return _to_jsonable(report)
