"""
Phase 2 — Data Cleaning.

Takes the raw dataframe plus the validation report already computed for
it, and produces a cleaned dataframe alongside a human-readable summary
of every action taken. Cleaning choices are intentionally conservative:
outliers are capped rather than deleted, and rows are only dropped when
a value genuinely can't be recovered (e.g. an unparseable order date).
"""
import numpy as np
import pandas as pd

from utils.schema_hints import (
    NUMERIC_FIELDS,
    DATE_FIELDS,
    CATEGORICAL_FIELDS,
    match_columns_to_fields,
)

OUTLIER_IQR_MULTIPLIER = 1.5
HIGH_MISSING_DROP_THRESHOLD = 0.6  # drop a column entirely past this missing ratio


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    rows_before, columns_before = df.shape
    actions: list[str] = []

    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    numeric_cols = {field_matches[f] for f in NUMERIC_FIELDS if field_matches.get(f)}
    date_cols = {field_matches[f] for f in DATE_FIELDS if field_matches.get(f)}
    categorical_cols = {field_matches[f] for f in CATEGORICAL_FIELDS if field_matches.get(f)}

    # --- 1. duplicate row removal ---
    duplicate_rows_removed = int(df.duplicated().sum())
    if duplicate_rows_removed:
        df = df.drop_duplicates(keep="first")
        actions.append(f"Removed {duplicate_rows_removed} fully duplicate row(s).")

    # --- 2. duplicate key removal ---
    duplicate_key_rows_removed = 0
    key_col = field_matches.get("order_id")
    if key_col and key_col in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=[key_col], keep="first")
        duplicate_key_rows_removed = before - len(df)
        if duplicate_key_rows_removed:
            actions.append(
                f"Removed {duplicate_key_rows_removed} row(s) with a duplicate '{key_col}'."
            )

    # --- 3. drop columns that are almost entirely empty ---
    dropped_columns = []
    for col in list(df.columns):
        missing_ratio = df[col].isna().mean()
        if missing_ratio >= HIGH_MISSING_DROP_THRESHOLD:
            dropped_columns.append(col)
            df = df.drop(columns=[col])
    if dropped_columns:
        actions.append(
            f"Dropped {len(dropped_columns)} column(s) that were mostly empty: "
            f"{', '.join(dropped_columns)}."
        )

    # --- 4. type correction: numeric columns stored as text ---
    type_conversions = {}
    for col in numeric_cols & set(df.columns):
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[,$₹%]", "", regex=True), errors="coerce"
            )
            type_conversions[col] = "text → numeric"

    # also opportunistically fix any other column that is >90% numeric-looking text
    for col in set(df.columns) - numeric_cols - date_cols:
        if df[col].dtype == object:
            non_null = df[col].dropna().astype(str)
            if non_null.empty:
                continue
            coerced = pd.to_numeric(
                non_null.str.replace(r"[,$₹%]", "", regex=True), errors="coerce"
            )
            if coerced.notna().mean() > 0.9:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r"[,$₹%]", "", regex=True), errors="coerce"
                )
                type_conversions[col] = "text → numeric"

    # --- 5. type correction: date columns stored as text, standardize format ---
    rows_dropped_missing_dates = 0
    for col in date_cols & set(df.columns):
        parsed = pd.to_datetime(df[col], errors="coerce")
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            type_conversions[col] = "text → date"
        before = len(df)
        df = df[parsed.notna() | df[col].isna()]  # drop only genuinely unparseable non-null dates
        parsed = parsed.loc[df.index]
        rows_dropped_missing_dates += before - len(df)
        df[col] = parsed.dt.strftime("%Y-%m-%d")
    if rows_dropped_missing_dates:
        actions.append(
            f"Removed {rows_dropped_missing_dates} row(s) with an unreadable date."
        )

    # --- 6. missing value handling ---
    missing_values_filled = {}
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            fill_value = float(df[col].median()) if df[col].notna().any() else 0.0
            df[col] = df[col].fillna(fill_value)
            missing_values_filled[col] = {
                "count": missing_count,
                "method": "median",
                "fill_value": round(fill_value, 2),
            }
        elif col in date_cols:
            continue  # date rows were already dropped above
        else:
            mode_series = df[col].mode(dropna=True)
            fill_value = mode_series.iloc[0] if not mode_series.empty else "Unknown"
            df[col] = df[col].fillna(fill_value)
            missing_values_filled[col] = {
                "count": missing_count,
                "method": "mode" if not mode_series.empty else "constant",
                "fill_value": str(fill_value),
            }
    if missing_values_filled:
        actions.append(
            f"Filled missing values in {len(missing_values_filled)} column(s): "
            f"{', '.join(missing_values_filled.keys())}."
        )

    # --- 7. outlier capping (winsorization) on key numeric fields ---
    outliers_capped = {}
    for col in numeric_cols & set(df.columns):
        series = df[col]
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - OUTLIER_IQR_MULTIPLIER * iqr
        upper = q3 + OUTLIER_IQR_MULTIPLIER * iqr
        capped_mask = (series < lower) | (series > upper)
        capped_count = int(capped_mask.sum())
        if capped_count:
            df[col] = series.clip(lower=lower, upper=upper)
            outliers_capped[col] = capped_count
    if outliers_capped:
        actions.append(
            f"Capped {sum(outliers_capped.values())} outlier value(s) across "
            f"{len(outliers_capped)} column(s) to the IQR bounds."
        )

    # --- 8. formatting: trim whitespace, title-case categorical text ---
    formatted_columns = []
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            if col in categorical_cols:
                df[col] = df[col].str.title()
            formatted_columns.append(col)
    if formatted_columns:
        actions.append(f"Standardized text formatting in {len(formatted_columns)} column(s).")

    df = df.reset_index(drop=True)
    rows_after, columns_after = df.shape

    summary = {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "columns_before": columns_before,
        "columns_after": columns_after,
        "duplicate_rows_removed": duplicate_rows_removed,
        "duplicate_key_rows_removed": duplicate_key_rows_removed,
        "rows_dropped_missing_dates": rows_dropped_missing_dates,
        "dropped_columns": dropped_columns,
        "type_conversions": type_conversions,
        "missing_values_filled": missing_values_filled,
        "outliers_capped": outliers_capped,
        "formatted_columns": formatted_columns,
        "actions": actions,
    }
    return df, summary
