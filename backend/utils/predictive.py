"""
Phase 5 — Predictive Analytics.

Four scikit-learn powered modules, each independent and each degrading
gracefully to `{"available": False, "reason": "..."}` when the dataset
doesn't have the columns or the row/customer count needed for a
trustworthy model — never a fabricated number.

All modules re-derive their own features from the cleaned (or raw)
dataframe using the retail schema hints; nothing here assumes a fixed
column layout beyond what's already been detected elsewhere in the app.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from utils.schema_hints import match_columns_to_fields

RANDOM_STATE = 42
MIN_ROWS_FOR_REGRESSION = 10
MIN_MONTHS_FOR_FORECAST = 3
MIN_CUSTOMERS_FOR_SEGMENTATION = 6
MIN_CUSTOMERS_FOR_CHURN = 10
HOLD_OUT_MIN_ROWS = 30
CHURN_RECENCY_PERCENTILE = 0.7


def _clean(value):
    if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 4)
    return value


def _unavailable(reason: str) -> dict:
    return {"available": False, "reason": reason}


def _prepare(df: pd.DataFrame, field_matches: dict) -> pd.DataFrame:
    df = df.copy()
    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# 1. Sales Prediction — regression on transaction-level revenue
# ---------------------------------------------------------------------------


def sales_prediction(df: pd.DataFrame, field_matches: dict) -> dict:
    df = _prepare(df, field_matches)
    revenue_col = field_matches.get("revenue")
    if not revenue_col or revenue_col not in df.columns:
        return _unavailable("No revenue column detected — sales prediction needs a revenue field.")

    feature_cols = []
    numeric_features = [f for f in (field_matches.get("quantity"), field_matches.get("unit_price")) if f and f in df.columns]
    categorical_features = [f for f in (field_matches.get("region"), field_matches.get("category")) if f and f in df.columns]

    working = df[[revenue_col] + numeric_features + categorical_features].copy()
    date_col = field_matches.get("order_date")
    if date_col and date_col in df.columns:
        working["order_month"] = df[date_col].dt.month
        working["order_dow"] = df[date_col].dt.dayofweek
        numeric_features = numeric_features + ["order_month", "order_dow"]

    working = working.dropna(subset=[revenue_col])
    if len(working) < MIN_ROWS_FOR_REGRESSION:
        return _unavailable(
            f"Only {len(working)} usable rows — need at least {MIN_ROWS_FOR_REGRESSION} for a reliable model."
        )

    y = working[revenue_col]
    X_numeric = working[numeric_features].fillna(working[numeric_features].median()) if numeric_features else pd.DataFrame(index=working.index)
    X_categorical = pd.get_dummies(working[categorical_features], drop_first=False) if categorical_features else pd.DataFrame(index=working.index)
    X = pd.concat([X_numeric, X_categorical], axis=1)

    if X.shape[1] == 0:
        return _unavailable("No usable predictor columns (quantity, price, region, category, or date) were detected.")

    use_holdout = len(working) >= HOLD_OUT_MIN_ROWS
    if use_holdout:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=RANDOM_STATE)
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    importances = sorted(
        zip(X.columns, model.feature_importances_), key=lambda t: t[1], reverse=True
    )[:10]

    sample = pd.DataFrame({"actual": y_test.values, "predicted": predictions}).head(15)

    return {
        "available": True,
        "validation_method": "held-out test set (25%)" if use_holdout else "trained on full sample (too small to hold out)",
        "rows_used": int(len(working)),
        "model": "RandomForestRegressor",
        "metrics": {
            "r2": _clean(r2_score(y_test, predictions)),
            "mae": _clean(mean_absolute_error(y_test, predictions)),
            "rmse": _clean(np.sqrt(mean_squared_error(y_test, predictions))),
        },
        "feature_importance": [{"feature": f, "importance": _clean(v)} for f, v in importances],
        "sample_predictions": [
            {"actual": _clean(a), "predicted": _clean(p)} for a, p in zip(sample["actual"], sample["predicted"])
        ],
    }


# ---------------------------------------------------------------------------
# 2. Revenue Forecasting — monthly trend extrapolation
# ---------------------------------------------------------------------------


def revenue_forecast(df: pd.DataFrame, field_matches: dict, periods: int = 3) -> dict:
    df = _prepare(df, field_matches)
    date_col = field_matches.get("order_date")
    revenue_col = field_matches.get("revenue")
    if not date_col or date_col not in df.columns:
        return _unavailable("No order date column detected — forecasting needs a time series.")
    if not revenue_col or revenue_col not in df.columns:
        return _unavailable("No revenue column detected — forecasting needs a revenue field.")

    working = df.dropna(subset=[date_col])
    if working.empty:
        return _unavailable("No valid order dates found.")

    monthly = working.set_index(date_col).resample("ME")[revenue_col].sum()
    monthly = monthly[monthly.index.notna()]
    if len(monthly) < MIN_MONTHS_FOR_FORECAST:
        return _unavailable(
            f"Only {len(monthly)} month(s) of history — need at least {MIN_MONTHS_FOR_FORECAST} to forecast a trend."
        )

    X = np.arange(len(monthly)).reshape(-1, 1)
    y = monthly.values
    model = LinearRegression()
    model.fit(X, y)
    fitted = model.predict(X)

    future_X = np.arange(len(monthly), len(monthly) + periods).reshape(-1, 1)
    raw_forecast = model.predict(future_X)
    forecast_values = np.clip(raw_forecast, a_min=0, a_max=None)  # revenue can't go negative
    was_clipped = bool((raw_forecast < 0).any())

    last_date = monthly.index[-1]
    forecast_dates = pd.date_range(last_date + pd.offsets.MonthEnd(1), periods=periods, freq="ME")

    notes = []
    if len(monthly) < 6:
        notes.append("Based on limited history — treat as a directional trend, not a precise prediction.")
    if was_clipped:
        notes.append(
            "The historical trend is declining steeply enough that the raw projection went "
            "negative for one or more months; those months are floored at 0 rather than shown "
            "as negative revenue."
        )

    return {
        "available": True,
        "method": "linear trend regression on monthly revenue",
        "months_of_history": int(len(monthly)),
        "note": " ".join(notes) or None,
        "metrics": {
            "r2_on_history": _clean(r2_score(y, fitted)),
            "mae_on_history": _clean(mean_absolute_error(y, fitted)),
        },
        "history": {
            "x": [d.strftime("%Y-%m") for d in monthly.index],
            "y": [_clean(v) for v in y],
        },
        "forecast": {
            "x": [d.strftime("%Y-%m") for d in forecast_dates],
            "y": [_clean(v) for v in forecast_values],
        },
    }


# ---------------------------------------------------------------------------
# Shared: per-customer aggregation used by segmentation and churn
# ---------------------------------------------------------------------------


def _customer_aggregates(df: pd.DataFrame, field_matches: dict) -> pd.DataFrame | None:
    customer_col = field_matches.get("customer")
    revenue_col = field_matches.get("revenue")
    date_col = field_matches.get("order_date")
    order_col = field_matches.get("order_id")

    if not customer_col or customer_col not in df.columns:
        return None

    agg = {}
    if revenue_col and revenue_col in df.columns:
        agg["total_revenue"] = (revenue_col, "sum")
    if order_col and order_col in df.columns:
        agg["order_count"] = (order_col, "nunique")
    else:
        agg["order_count"] = (customer_col, "count")
    if date_col and date_col in df.columns:
        agg["first_order"] = (date_col, "min")
        agg["last_order"] = (date_col, "max")

    grouped = df.groupby(customer_col).agg(**agg).reset_index()

    if "total_revenue" in grouped.columns and "order_count" in grouped.columns:
        grouped["avg_order_value"] = grouped["total_revenue"] / grouped["order_count"].replace(0, np.nan)
    return grouped


# ---------------------------------------------------------------------------
# 3. Customer Segmentation — KMeans on RFM-style features
# ---------------------------------------------------------------------------


def customer_segmentation(df: pd.DataFrame, field_matches: dict) -> dict:
    df = _prepare(df, field_matches)
    customer_col = field_matches.get("customer")
    grouped = _customer_aggregates(df, field_matches)

    if grouped is None:
        return _unavailable("No customer column detected — segmentation needs a customer field.")
    if "total_revenue" not in grouped.columns:
        return _unavailable("No revenue column detected — segmentation needs revenue per customer.")

    n_customers = len(grouped)
    if n_customers < MIN_CUSTOMERS_FOR_SEGMENTATION:
        return _unavailable(
            f"Only {n_customers} distinct customer(s) — need at least {MIN_CUSTOMERS_FOR_SEGMENTATION} to segment."
        )

    has_recency = "last_order" in grouped.columns
    if has_recency:
        max_date = grouped["last_order"].max()
        grouped["recency_days"] = (max_date - grouped["last_order"]).dt.days

    feature_cols = [c for c in ["total_revenue", "order_count", "avg_order_value", "recency_days"] if c in grouped.columns]
    features = grouped[feature_cols].fillna(0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    k = 3 if n_customers >= 9 else 2
    kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    grouped["cluster"] = kmeans.fit_predict(scaled)

    sil_score = None
    if n_customers > k:
        try:
            sil_score = _clean(silhouette_score(scaled, grouped["cluster"]))
        except ValueError:
            sil_score = None

    cluster_stats = grouped.groupby("cluster")[feature_cols].mean()
    ranked = cluster_stats["total_revenue"].sort_values(ascending=False).index.tolist()

    if k == 3:
        label_map = {ranked[0]: "High-Value Customers", ranked[1]: "Regular Customers", ranked[2]: "Occasional Shoppers"}
    else:
        label_map = {ranked[0]: "High-Value Customers", ranked[1]: "Occasional Shoppers"}

    if has_recency:
        most_at_risk = cluster_stats["recency_days"].idxmax()
        if label_map.get(most_at_risk) != "High-Value Customers":
            label_map[most_at_risk] = "At-Risk Customers"

    segments = []
    for cluster_id, stats in cluster_stats.iterrows():
        segments.append(
            {
                "cluster": int(cluster_id),
                "label": label_map.get(cluster_id, f"Segment {cluster_id}"),
                "size": int((grouped["cluster"] == cluster_id).sum()),
                "avg_total_revenue": _clean(stats.get("total_revenue")),
                "avg_order_count": _clean(stats.get("order_count")),
                "avg_order_value": _clean(stats.get("avg_order_value")),
                "avg_recency_days": _clean(stats.get("recency_days")) if has_recency else None,
            }
        )
    segments.sort(key=lambda s: s["avg_total_revenue"], reverse=True)

    scatter = [
        {
            "customer": str(row[customer_col]),
            "total_revenue": _clean(row["total_revenue"]),
            "order_count": _clean(row["order_count"]),
            "cluster": int(row["cluster"]),
            "label": label_map.get(row["cluster"], f"Segment {row['cluster']}"),
        }
        for _, row in grouped.iterrows()
    ][:300]

    return {
        "available": True,
        "model": "KMeans",
        "n_customers": n_customers,
        "n_clusters": k,
        "silhouette_score": sil_score,
        "segments": segments,
        "scatter": scatter,
    }


# ---------------------------------------------------------------------------
# 4. Customer Churn Prediction
# ---------------------------------------------------------------------------


def churn_prediction(df: pd.DataFrame, field_matches: dict) -> dict:
    df = _prepare(df, field_matches)
    customer_col = field_matches.get("customer")
    date_col = field_matches.get("order_date")
    grouped = _customer_aggregates(df, field_matches)

    if grouped is None:
        return _unavailable("No customer column detected — churn prediction needs a customer field.")
    if not date_col or "last_order" not in grouped.columns:
        return _unavailable("No order date column detected — churn prediction needs purchase history over time.")

    n_customers = len(grouped)
    if n_customers < MIN_CUSTOMERS_FOR_CHURN:
        return _unavailable(
            f"Only {n_customers} distinct customer(s) — need at least {MIN_CUSTOMERS_FOR_CHURN} to model churn."
        )

    max_date = grouped["last_order"].max()
    grouped["recency_days"] = (max_date - grouped["last_order"]).dt.days
    grouped["tenure_days"] = (grouped["last_order"] - grouped["first_order"]).dt.days
    grouped["avg_days_between_orders"] = grouped.apply(
        lambda r: r["tenure_days"] / r["order_count"] if r["order_count"] > 1 else r["tenure_days"], axis=1
    )

    churn_cutoff = grouped["recency_days"].quantile(CHURN_RECENCY_PERCENTILE)
    grouped["churned"] = (grouped["recency_days"] > churn_cutoff).astype(int)

    feature_cols = [c for c in ["total_revenue", "order_count", "avg_order_value", "tenure_days", "avg_days_between_orders"] if c in grouped.columns]
    X = grouped[feature_cols].fillna(0)
    y = grouped["churned"]

    if y.nunique() < 2:
        return _unavailable("Could not form two churn groups from this data's purchase pattern.")

    use_holdout = n_customers >= 20
    if use_holdout:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=RANDOM_STATE, class_weight="balanced")
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    cm = confusion_matrix(y_test, predictions, labels=[0, 1]).tolist()
    importances = sorted(zip(feature_cols, model.feature_importances_), key=lambda t: t[1], reverse=True)

    all_probabilities = model.predict_proba(X)[:, 1]
    grouped["churn_probability"] = all_probabilities
    at_risk = grouped.sort_values("churn_probability", ascending=False).head(10)

    return {
        "available": True,
        "model": "RandomForestClassifier",
        "validation_method": "held-out test set (25%, stratified)" if use_holdout else "trained on full sample (too small to hold out)",
        "churn_definition": (
            f"A customer is labeled 'churned' if their most recent order is older than the "
            f"{int(CHURN_RECENCY_PERCENTILE * 100)}th percentile of recency across all customers "
            f"({_clean(churn_cutoff)} days) — a relative cutoff derived from this dataset's own "
            f"purchase cadence, not a fixed calendar rule."
        ),
        "churn_rate_percent": _clean(grouped["churned"].mean() * 100),
        "n_customers": n_customers,
        "metrics": {
            "accuracy": _clean(accuracy_score(y_test, predictions)),
            "precision": _clean(precision_score(y_test, predictions, zero_division=0)),
            "recall": _clean(recall_score(y_test, predictions, zero_division=0)),
            "f1": _clean(f1_score(y_test, predictions, zero_division=0)),
        },
        "confusion_matrix": cm,
        "feature_importance": [{"feature": f, "importance": _clean(v)} for f, v in importances],
        "at_risk_customers": [
            {
                "customer": str(row[customer_col]),
                "churn_probability": _clean(row["churn_probability"]),
                "recency_days": _clean(row["recency_days"]),
                "total_revenue": _clean(row.get("total_revenue")),
            }
            for _, row in at_risk.iterrows()
        ],
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def generate_predictive_report(df: pd.DataFrame) -> dict:
    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    return {
        "schema_match": field_matches,
        "sales_prediction": sales_prediction(df, field_matches),
        "revenue_forecast": revenue_forecast(df, field_matches),
        "customer_segmentation": customer_segmentation(df, field_matches),
        "churn_prediction": churn_prediction(df, field_matches),
    }
