from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Dataset, ChatMessage
from routes.datasets import _load_best_dataframe  # reuse the same cleaned/raw file resolution
from utils.schema_hints import match_columns_to_fields
from utils.dashboard import build_dashboard
from utils.ask_context import build_dataset_context, build_system_prompt
from utils.anthropic_client import ask_claude

chat_bp = Blueprint("chat", __name__, url_prefix="/api/datasets")


def _get_owned_dataset(dataset_id, user_id):
    return Dataset.query.filter_by(id=dataset_id, user_id=user_id).first_or_404()


@chat_bp.get("/<int:dataset_id>/messages")
@jwt_required()
def get_messages(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = _get_owned_dataset(dataset_id, user_id)
    return jsonify({"messages": [m.to_dict() for m in dataset.chat_messages]}), 200


@chat_bp.delete("/<int:dataset_id>/messages")
@jwt_required()
def clear_messages(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = _get_owned_dataset(dataset_id, user_id)

    for message in list(dataset.chat_messages):
        db.session.delete(message)
    db.session.commit()

    return jsonify({"message": "Conversation cleared."}), 200


@chat_bp.post("/<int:dataset_id>/ask")
@jwt_required()
def ask(dataset_id):
    user_id = int(get_jwt_identity())
    dataset = _get_owned_dataset(dataset_id, user_id)

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"errors": ["Ask a question first."]}), 400
    if len(question) > 2000:
        return jsonify({"errors": ["That question is too long (max 2000 characters)."]}), 400

    df, stage, error = _load_best_dataframe(dataset)
    if error:
        return jsonify({"errors": [error]}), 404
    if df.empty:
        return jsonify({"errors": ["No data available to answer questions about."]}), 400

    field_matches = match_columns_to_fields([str(c) for c in df.columns])
    dashboard_data = build_dashboard(df, {})

    dataset_meta = {"filename": dataset.original_filename, "row_count": int(len(df)), "source_stage": stage}
    context_text = build_dataset_context(
        df, field_matches, dashboard_data, dataset.insights_report, dataset.predictive_report, dataset_meta
    )
    system_prompt = build_system_prompt(context_text)

    history_limit = current_app.config["ASK_MAX_HISTORY_MESSAGES"]
    prior_messages = dataset.chat_messages[-history_limit:]
    conversation = [{"role": m.role, "content": m.content} for m in prior_messages]
    conversation.append({"role": "user", "content": question})

    answer, ask_error = ask_claude(
        system_prompt=system_prompt,
        messages=conversation,
        api_key=current_app.config["ANTHROPIC_API_KEY"],
        model=current_app.config["ANTHROPIC_MODEL"],
        max_tokens=current_app.config["ANTHROPIC_MAX_TOKENS"],
        api_url=current_app.config["ANTHROPIC_API_URL"],
    )

    if ask_error:
        return jsonify({"errors": [ask_error]}), 502

    user_message = ChatMessage(dataset_id=dataset.id, role="user", content=question)
    assistant_message = ChatMessage(dataset_id=dataset.id, role="assistant", content=answer)
    db.session.add_all([user_message, assistant_message])
    db.session.commit()

    return jsonify({"user_message": user_message.to_dict(), "assistant_message": assistant_message.to_dict()}), 200
