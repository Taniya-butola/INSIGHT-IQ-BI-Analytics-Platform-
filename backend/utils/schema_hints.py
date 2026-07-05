"""
Heuristics for recognizing common retail-sales columns by name, so the
validation report can tell a user "we couldn't find a revenue column"
instead of silently ignoring the whole idea of a schema. This is
intentionally soft: nothing here rejects a file, it only informs the
report and gives cleaning stage-specific type coercion hints.
"""
import re

# canonical_field -> regex patterns tried (case-insensitive) against column names
RETAIL_FIELD_PATTERNS = {
    "order_id": [r"order.?id", r"^id$", r"invoice.?(no|number|id)", r"transaction.?id"],
    "order_date": [r"order.?date", r"^date$", r"purchase.?date", r"invoice.?date"],
    "customer": [r"customer", r"client", r"buyer"],
    "product": [r"product", r"item", r"sku"],
    "category": [r"category", r"product.?type", r"segment"],
    "region": [r"region", r"state", r"city", r"territory", r"location"],
    "quantity": [r"qty", r"quantity", r"units?.?sold", r"units?$"],
    "unit_price": [r"unit.?price", r"price$", r"rate"],
    "revenue": [r"revenue", r"sales.?amount", r"total.?amount", r"^sales$", r"amount$"],
    "profit": [r"profit", r"margin"],
    "stock": [r"stock", r"inventory", r"on.?hand", r"available.?(qty|units|stock)"],
}

# canonical_field -> expected data "shape" used during cleaning
NUMERIC_FIELDS = {"quantity", "unit_price", "revenue", "profit", "stock"}
DATE_FIELDS = {"order_date"}
CATEGORICAL_FIELDS = {"customer", "product", "category", "region"}


def match_columns_to_fields(columns: list[str]) -> dict[str, str | None]:
    """Returns {canonical_field: matched_column_name_or_None} for each known field."""
    matches: dict[str, str | None] = {field: None for field in RETAIL_FIELD_PATTERNS}
    for field, patterns in RETAIL_FIELD_PATTERNS.items():
        for col in columns:
            normalized = col.strip().lower().replace(" ", "_").replace("-", "_")
            if any(re.search(p, normalized) for p in patterns):
                matches[field] = col
                break
    return matches
