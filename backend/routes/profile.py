from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@profile_bp.get("")
@jwt_required()
def get_profile():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify({"user": user.to_dict()}), 200


@profile_bp.put("")
@jwt_required()
def update_profile():
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    if full_name:
        if len(full_name) < 2:
            return jsonify({"errors": ["Full name must be at least 2 characters."]}), 400
        user.full_name = full_name

    if "company_name" in data:
        user.company_name = (data.get("company_name") or "").strip() or None

    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200


@profile_bp.put("/password")
@jwt_required()
def change_password():
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}

    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not user.check_password(current_password):
        return jsonify({"errors": ["Current password is incorrect."]}), 400
    if len(new_password) < 8:
        return jsonify({"errors": ["New password must be at least 8 characters."]}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated."}), 200
