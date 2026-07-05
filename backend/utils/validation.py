"""
Phase 2 — Data Validation.

Runs a battery of structural and content checks against a raw uploaded
dataframe and returns a JSON-serializable report. Nothing here mutates
the data; cleaning.py consumes this report to decide what to fix.
"""
import pandas as pd

from utils.schema_hints import NUMERIC_FIELDS, DATE_FIELDS, match_columns_to_fields

MAX_SAMPLE_VALUES = 4
OUTLIER_IQR_MULTIPLIER = 1.5


def _infer_semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    non_null = series.dropna()
    if non_null.empty:
        return "text"
    # try coercing a sample to numeric / date to catch "numbers stored as text"
    sample = non_null.astype(str).head(50)
    numeric_ok = pd.to_numeric(
        sample.str.replace(r"[,$₹%]", "", regex=True), errors="coerce"
    ).notna().mean()
    if numeric_ok > 0.9:
        return "numeric_as_text"
    date_ok = pd.to_datetime(sample, errors="coerce").notna().mean()
    if date_ok > 0.9:
        return "date_as_text"
    if non_null.nunique() <= max(20, len(non_null) * 0.05):
        return "categorical"
    return "text"


def _sample_values(series: pd.Series):
    vals = series.dropna().unique()[:MAX_SAMPLE_VALUES]
    return [str(v) for v in vals]


def _detect_outliers_iqr(series: pd.Series) -> int:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 4:
        return 0
    q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower = q1 - OUTLIER_IQR_MULTIPLIER * iqr
    upper = q3 + OUTLIER_IQR_MULTIPLIER * iqr
    return int(((numeric < lower) | (numeric > upper)).sum())


def validate_dataframe(df: pd.DataFrame, file_extension: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    row_count, column_count = df.shape

    # --- structural checks ---
    if file_extension not in {"csv", "xlsx"}:
        errors.append(f"Unsupported file format: {file_extension}")

    if row_count == 0:
        errors.append("Dataset contains no rows.")

    blank_columns = [c for c in df.columns if str(c).strip() == "" or str(c).startswith("Unnamed")]
    if blank_columns:
        warnings.append(f"{len(blank_columns)} column(s) have no header name.")

    duplicate_column_names = df.columns[df.columns.duplicated()].tolist()
    if duplicate_column_names:
        errors.append(
            f"Duplicate column names found: {', '.join(map(str, set(duplicate_column_names)))}"
        )

    # --- schema recognition (retail domain) ---
    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    missing_recommended = [f for f, col in field_matches.items() if col is None]
    if missing_recommended:
        warnings.append(
            f"{len(missing_recommended)} recommended retail column(s) not detected: "
            f"{', '.join(missing_recommended)}. Dashboards relying on these will be limited."
        )

    # --- duplicate rows ---
    duplicate_row_count = int(df.duplicated().sum())
    if duplicate_row_count > 0:
        warnings.append(f"{duplicate_row_count} fully duplicate row(s) found.")

    duplicate_key_info = None
    key_col = field_matches.get("order_id")
    if key_col and key_col in df.columns:
        dup_keys = int(df[key_col].duplicated().sum())
        duplicate_key_info = {"key_column": key_col, "duplicate_count": dup_keys}
        if dup_keys > 0:
            warnings.append(f"{dup_keys} duplicate value(s) found in key column '{key_col}'.")

    # --- per-column analysis ---
    numeric_canonical_cols = {field_matches[f] for f in NUMERIC_FIELDS if field_matches.get(f)}
    date_canonical_cols = {field_matches[f] for f in DATE_FIELDS if field_matches.get(f)}

    columns_report = []
    invalid_negative = {}
    invalid_dates = {}
    outliers = {}

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = round(missing_count / row_count * 100, 2) if row_count else 0.0
        semantic_type = _infer_semantic_type(series)
        issues = []

        if missing_pct > 0:
            severity = "high" if missing_pct > 30 else "low"
            issues.append(f"{missing_count} missing value(s) ({missing_pct}%)")
            if severity == "high":
                warnings.append(f"Column '{col}' is missing {missing_pct}% of values.")

        if col in numeric_canonical_cols or semantic_type in ("numeric", "numeric_as_text"):
            numeric_series = pd.to_numeric(
                series.astype(str).str.replace(r"[,$₹%]", "", regex=True), errors="coerce"
            )
            non_numeric_count = int(series.notna().sum() - numeric_series.notna().sum())
            if non_numeric_count > 0:
                issues.append(f"{non_numeric_count} value(s) could not be read as numbers")

            if col in numeric_canonical_cols and col in [
                field_matches.get("quantity"),
                field_matches.get("unit_price"),
                field_matches.get("revenue"),
            ]:
                negative_count = int((numeric_series < 0).sum())
                if negative_count > 0:
                    issues.append(f"{negative_count} negative value(s)")
                    invalid_negative[col] = negative_count

            outlier_count = _detect_outliers_iqr(numeric_series)
            if outlier_count > 0:
                issues.append(f"{outlier_count} statistical outlier(s) (IQR method)")
                outliers[col] = outlier_count

        if col in date_canonical_cols or semantic_type in ("date", "date_as_text"):
            parsed = pd.to_datetime(series, errors="coerce")
            unparseable = int(series.notna().sum() - parsed.notna().sum())
            if unparseable > 0:
                issues.append(f"{unparseable} value(s) could not be read as dates")
                invalid_dates[col] = unparseable

        columns_report.append(
            {
                "name": str(col),
                "dtype": str(series.dtype),
                "inferred_type": semantic_type,
                "missing_count": missing_count,
                "missing_percentage": missing_pct,
                "unique_count": int(series.nunique(dropna=True)),
                "sample_values": _sample_values(series),
                "issues": issues,
            }
        )

    overall_status = "failed" if errors else ("passed_with_warnings" if warnings else "passed")

    return {
        "overall_status": overall_status,
        "row_count": row_count,
        "column_count": column_count,
        "schema_match": field_matches,
        "missing_recommended_columns": missing_recommended,
        "duplicate_rows": {
            "count": duplicate_row_count,
            "percentage": round(duplicate_row_count / row_count * 100, 2) if row_count else 0.0,
        },
        "duplicate_key": duplicate_key_info,
        "invalid_values": {
            "negative_numeric": invalid_negative,
            "unparseable_dates": invalid_dates,
        },
        "outliers": outliers,
        "columns": columns_report,
        "errors": errors,
        "warnings": warnings,
    }
