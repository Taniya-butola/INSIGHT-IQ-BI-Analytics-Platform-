import os
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from extensions import db
from models import Dataset
from utils.validators import allowed_file
from utils.validation import validate_dataframe
from utils.cleaning import clean_dataframe
from utils.eda import generate_eda
from utils.dashboard import get_filter_options, build_dashboard
from utils.schema_hints import match_columns_to_fields
from utils.predictive import generate_predictive_report
from utils.insights import generate_insights
from utils.reports_data import build_report_context, REPORT_TYPES
from utils.reports_pdf import build_pdf
from utils.reports_xlsx import build_xlsx

datasets_bp = Blueprint("datasets", __name__, url_prefix="/api/datasets")

MAX_PREVIEW_COLUMNS = 50
PREVIEW_ROW_LIMIT = 25


def _read_dataframe(filepath: str, extension: str) -> pd.DataFrame:
    if extension == "csv":
        return pd.read_csv(filepath)
    return pd.read_excel(filepath)


def _user_folder(user_id: int) -> str:
    return os.path.join(current_app.config["UPLOAD_FOLDER"], str(user_id))


def _raw_filepath(dataset: Dataset) -> str:
    return os.path.join(_user_folder(dataset.user_id), dataset.stored_filename)


def _cleaned_filepath(dataset: Dataset) -> str | None:
    if not dataset.cleaned_filename:
        return None
    return os.path.join(_user_folder(dataset.user_id), dataset.cleaned_filename)


def _rows_to_json(df: pd.DataFrame, limit: int) -> list[dict]:
    """Converts a preview slice to JSON-safe records (NaN/NaT -> None)."""
    preview = df.head(limit).replace({np.nan: None})
    return preview.astype(object).where(pd.notnull(preview), None).to_dict(orient="records")


def _load_best_dataframe(dataset: Dataset) -> tuple[pd.DataFrame | None, str, str | None]:
    """Returns (df, stage, error_message). stage is 'cleaned' or 'raw'."""
    cleaned_path = _cleaned_filepath(dataset)
    if cleaned_path and os.path.exists(cleaned_path):
        try:
            return pd.read_csv(cleaned_path), "cleaned", None
        except Exception as exc:
            return None, "cleaned", f"Could not read cleaned file: {exc}"

    raw_path = _raw_filepath(dataset)
    if not os.path.exists(raw_path):
        return None, "raw", "The uploaded file is missing on disk."
    try:
        return _read_dataframe(raw_path, dataset.file_extension), "raw", None
    except Exception as exc:
        return None, "raw", f"Could not re-read file: {exc}"


@datasets_bp.post("/upload")
@jwt_required()
def upload_dataset():
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"errors": ["No file was included in the request."]}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"errors": ["No file was selected."]}), 400

    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    if not allowed_file(file.filename, allowed):
        return jsonify(
            {"errors": [f"Unsupported file type. Allowed: {', '.join(sorted(allowed))}."]}
        ), 400

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{extension}"

    user_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    filepath = os.path.join(user_folder, stored_filename)
    file.save(filepath)

    file_size = os.path.getsize(filepath)

    # --- Basic structural validation (full validation pipeline = Phase 2) ---
    try:
        df = _read_dataframe(filepath, extension)
    except Exception as exc:  # malformed CSV/XLSX
        os.remove(filepath)
        return jsonify({"errors": [f"Could not parse file: {exc}"]}), 400

    if df.empty:
        os.remove(filepath)
        return jsonify({"errors": ["The uploaded file contains no data rows."]}), 400

    columns_preview = [
        {"name": str(col), "dtype": str(df[col].dtype)}
        for col in df.columns[:MAX_PREVIEW_COLUMNS]
    ]

    dataset = Dataset(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_extension=extension,
        file_size_bytes=file_size,
        row_count=int(df.shape[0]),
        column_count=int(df.shape[1]),
        columns_preview=columns_preview,
        status="uploaded",
    )
    db.session.add(dataset)
    db.session.commit()

    return jsonify({"dataset": dataset.to_dict()}), 201


@datasets_bp.get("")
@jwt_required()
def list_datasets():
    user_id = int(get_jwt_identity())
    datasets = (
        Dataset.query.filter_by(user_id=user_id)
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )
    return jsonify({"datasets": [d.to_dict() for d in datasets]}), 200


@datasets_bp.get("/<int:dataset_id>")
@jwt_required()
def get_dataset(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()
    return jsonify({"dataset": dataset.to_dict()}), 200


@datasets_bp.delete("/<int:dataset_id>")
@jwt_required()
def delete_dataset(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    for path in (_raw_filepath(dataset), _cleaned_filepath(dataset)):
        if path and os.path.exists(path):
            os.remove(path)

    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"message": "Dataset deleted."}), 200


# ---------------------------------------------------------------------------
# Phase 2 — Data Validation
# ---------------------------------------------------------------------------


@datasets_bp.post("/<int:dataset_id>/validate")
@jwt_required()
def validate_dataset(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    filepath = _raw_filepath(dataset)
    if not os.path.exists(filepath):
        return jsonify({"errors": ["The original uploaded file is missing on disk."]}), 404

    try:
        df = _read_dataframe(filepath, dataset.file_extension)
    except Exception as exc:
        return jsonify({"errors": [f"Could not re-read file: {exc}"]}), 400

    report = validate_dataframe(df, dataset.file_extension)

    dataset.validation_report = report
    dataset.validated_at = datetime.now(timezone.utc)
    dataset.status = "failed" if report["overall_status"] == "failed" else "validated"
    db.session.commit()

    return jsonify({"dataset": dataset.to_dict(), "validation_report": report}), 200


@datasets_bp.get("/<int:dataset_id>/validation")
@jwt_required()
def get_validation(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if dataset.validation_report is None:
        return jsonify({"errors": ["This dataset has not been validated yet."]}), 404

    return jsonify(
        {
            "validation_report": dataset.validation_report,
            "validated_at": dataset.validated_at.isoformat() if dataset.validated_at else None,
        }
    ), 200


# ---------------------------------------------------------------------------
# Phase 2 — Data Cleaning
# ---------------------------------------------------------------------------


@datasets_bp.post("/<int:dataset_id>/clean")
@jwt_required()
def clean_dataset(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if dataset.validation_report is None:
        return jsonify({"errors": ["Run validation before cleaning this dataset."]}), 400

    filepath = _raw_filepath(dataset)
    if not os.path.exists(filepath):
        return jsonify({"errors": ["The original uploaded file is missing on disk."]}), 404

    try:
        df = _read_dataframe(filepath, dataset.file_extension)
    except Exception as exc:
        return jsonify({"errors": [f"Could not re-read file: {exc}"]}), 400

    cleaned_df, summary = clean_dataframe(df)

    cleaned_filename = f"{uuid.uuid4().hex}_cleaned.csv"
    cleaned_filepath = os.path.join(_user_folder(user_id), cleaned_filename)
    cleaned_df.to_csv(cleaned_filepath, index=False)

    # remove the previous cleaned file, if any, before pointing at the new one
    old_cleaned = _cleaned_filepath(dataset)
    if old_cleaned and os.path.exists(old_cleaned):
        os.remove(old_cleaned)

    dataset.cleaning_summary = summary
    dataset.cleaned_filename = cleaned_filename
    dataset.cleaned_row_count = int(cleaned_df.shape[0])
    dataset.cleaned_column_count = int(cleaned_df.shape[1])
    dataset.cleaned_at = datetime.now(timezone.utc)
    dataset.status = "cleaned"
    db.session.commit()

    return jsonify({"dataset": dataset.to_dict(), "cleaning_summary": summary}), 200


@datasets_bp.get("/<int:dataset_id>/cleaning")
@jwt_required()
def get_cleaning(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if dataset.cleaning_summary is None:
        return jsonify({"errors": ["This dataset has not been cleaned yet."]}), 404

    return jsonify(
        {
            "cleaning_summary": dataset.cleaning_summary,
            "cleaned_at": dataset.cleaned_at.isoformat() if dataset.cleaned_at else None,
            "cleaned_row_count": dataset.cleaned_row_count,
            "cleaned_column_count": dataset.cleaned_column_count,
        }
    ), 200


# ---------------------------------------------------------------------------
# Row preview (raw or cleaned)
# ---------------------------------------------------------------------------


@datasets_bp.get("/<int:dataset_id>/preview")
@jwt_required()
def preview_dataset(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    stage = request.args.get("stage", "raw")
    if stage == "cleaned":
        filepath = _cleaned_filepath(dataset)
        if not filepath or not os.path.exists(filepath):
            return jsonify({"errors": ["This dataset has not been cleaned yet."]}), 404
        df = pd.read_csv(filepath)
    else:
        filepath = _raw_filepath(dataset)
        if not os.path.exists(filepath):
            return jsonify({"errors": ["The original uploaded file is missing on disk."]}), 404
        df = _read_dataframe(filepath, dataset.file_extension)

    return jsonify(
        {
            "stage": stage,
            "columns": [str(c) for c in df.columns],
            "rows": _rows_to_json(df, PREVIEW_ROW_LIMIT),
            "total_rows": int(df.shape[0]),
            "shown_rows": min(PREVIEW_ROW_LIMIT, int(df.shape[0])),
        }
    ), 200


# ---------------------------------------------------------------------------
# Phase 3 — Exploratory Data Analysis
# ---------------------------------------------------------------------------


@datasets_bp.post("/<int:dataset_id>/eda")
@jwt_required()
def run_eda(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    cleaned_path = _cleaned_filepath(dataset)
    used_stage = "cleaned"
    if cleaned_path and os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
    else:
        used_stage = "raw"
        raw_path = _raw_filepath(dataset)
        if not os.path.exists(raw_path):
            return jsonify({"errors": ["The uploaded file is missing on disk."]}), 404
        try:
            df = _read_dataframe(raw_path, dataset.file_extension)
        except Exception as exc:
            return jsonify({"errors": [f"Could not re-read file: {exc}"]}), 400

    if df.empty:
        return jsonify({"errors": ["No data available to analyze."]}), 400

    report = generate_eda(df)
    report["source_stage"] = used_stage

    dataset.eda_report = report
    dataset.eda_at = datetime.now(timezone.utc)
    dataset.status = "analyzed"
    db.session.commit()

    return jsonify({"dataset": dataset.to_dict(), "eda_report": report}), 200


@datasets_bp.get("/<int:dataset_id>/eda")
@jwt_required()
def get_eda(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if dataset.eda_report is None:
        return jsonify({"errors": ["This dataset has not been analyzed yet."]}), 404

    return jsonify(
        {
            "eda_report": dataset.eda_report,
            "eda_at": dataset.eda_at.isoformat() if dataset.eda_at else None,
        }
    ), 200


# ---------------------------------------------------------------------------
# Phase 4 — Interactive Dashboard
# ---------------------------------------------------------------------------


@datasets_bp.get("/<int:dataset_id>/dashboard/filters")
@jwt_required()
def dashboard_filters(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    df, stage, error = _load_best_dataframe(dataset)
    if error:
        return jsonify({"errors": [error]}), 404

    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    options = get_filter_options(df, field_matches)
    return jsonify({"stage": stage, "filters": options}), 200


@datasets_bp.get("/<int:dataset_id>/dashboard")
@jwt_required()
def dashboard(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    df, stage, error = _load_best_dataframe(dataset)
    if error:
        return jsonify({"errors": [error]}), 404
    if df.empty:
        return jsonify({"errors": ["No data available to build a dashboard."]}), 400

    filters = {
        "region": request.args.get("region") or None,
        "category": request.args.get("category") or None,
        "date_from": request.args.get("date_from") or None,
        "date_to": request.args.get("date_to") or None,
    }

    report = build_dashboard(df, filters)
    report["source_stage"] = stage

    return jsonify({"dashboard": report}), 200


# ---------------------------------------------------------------------------
# Phase 5 — Predictive Analytics
# ---------------------------------------------------------------------------


@datasets_bp.post("/<int:dataset_id>/predictive")
@jwt_required()
def run_predictive(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    df, stage, error = _load_best_dataframe(dataset)
    if error:
        return jsonify({"errors": [error]}), 404
    if df.empty:
        return jsonify({"errors": ["No data available to model."]}), 400

    report = generate_predictive_report(df)
    report["source_stage"] = stage

    dataset.predictive_report = report
    dataset.predictive_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"dataset": dataset.to_dict(), "predictive_report": report}), 200


@datasets_bp.get("/<int:dataset_id>/predictive")
@jwt_required()
def get_predictive(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if dataset.predictive_report is None:
        return jsonify({"errors": ["Predictive models have not been run yet."]}), 404

    return jsonify(
        {
            "predictive_report": dataset.predictive_report,
            "predictive_at": dataset.predictive_at.isoformat() if dataset.predictive_at else None,
        }
    ), 200


# ---------------------------------------------------------------------------
# Phase 6 — Business Insights
# ---------------------------------------------------------------------------


@datasets_bp.post("/<int:dataset_id>/insights")
@jwt_required()
def run_insights(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    df, stage, error = _load_best_dataframe(dataset)
    if error:
        return jsonify({"errors": [error]}), 404
    if df.empty:
        return jsonify({"errors": ["No data available to generate insights."]}), 400

    report = generate_insights(df)
    report["source_stage"] = stage

    dataset.insights_report = report
    dataset.insights_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"dataset": dataset.to_dict(), "insights_report": report}), 200


@datasets_bp.get("/<int:dataset_id>/insights")
@jwt_required()
def get_insights(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if dataset.insights_report is None:
        return jsonify({"errors": ["Insights have not been generated yet."]}), 404

    return jsonify(
        {
            "insights_report": dataset.insights_report,
            "insights_at": dataset.insights_at.isoformat() if dataset.insights_at else None,
        }
    ), 200


# ---------------------------------------------------------------------------
# Phase 7 — Report Generation
# ---------------------------------------------------------------------------


@datasets_bp.get("/<int:dataset_id>/reports/<report_type>")
@jwt_required()
def generate_report(dataset_id, report_type):
    user_id = int(get_jwt_identity())
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()

    if report_type not in REPORT_TYPES:
        return jsonify({"errors": [f"Unknown report type. Choose from: {', '.join(REPORT_TYPES)}"]}), 400

    fmt = request.args.get("format", "pdf").lower()
    if fmt not in ("pdf", "xlsx"):
        return jsonify({"errors": ["format must be 'pdf' or 'xlsx'."]}), 400

    df, stage, error = _load_best_dataframe(dataset)
    if error:
        return jsonify({"errors": [error]}), 404
    if df.empty:
        return jsonify({"errors": ["No data available to generate a report."]}), 400

    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    dashboard_data = build_dashboard(df, {})
    dashboard_data["source_stage"] = stage

    dataset_meta = {"filename": dataset.original_filename, "row_count": int(len(df)), "source_stage": stage}
    context = build_report_context(
        report_type, dashboard_data, dataset.insights_report, dataset.predictive_report, dataset_meta
    )

    safe_name = dataset.original_filename.rsplit(".", 1)[0]
    filename = f"{safe_name}_{report_type}.{fmt}"

    if fmt == "pdf":
        file_bytes = build_pdf(context)
        mimetype = "application/pdf"
    else:
        file_bytes = build_xlsx(context, df, field_matches)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return Response(
        file_bytes,
        mimetype=mimetype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@datasets_bp.get("/report-types")
@jwt_required()
def list_report_types():
    return jsonify({"report_types": [{"slug": k, "label": v} for k, v in REPORT_TYPES.items()]}), 200
