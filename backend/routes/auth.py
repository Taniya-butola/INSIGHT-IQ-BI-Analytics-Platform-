from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from extensions import db
from models import User
from utils.validators import validate_registration_payload, validate_login_payload

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    errors = validate_registration_payload(data)
    email = (data.get("email") or "").strip().lower()

    if not errors and User.query.filter_by(email=email).first():
        errors.append("An account with this email already exists.")

    if errors:
        return jsonify({"errors": errors}), 400

    user = User(
        full_name=data["full_name"].strip(),
        company_name=(data.get("company_name") or "").strip() or None,
        email=email,
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    errors = validate_login_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    email = data["email"].strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"errors": ["Invalid email or password."]}), 401

    if not user.is_active:
        return jsonify({"errors": ["This account has been disabled."]}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # Stateless JWTs: the client discards the token. A token blocklist
    # (e.g. Redis) can be added here later for true server-side revocation.
    return jsonify({"message": "Logged out."}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify({"user": user.to_dict()}), 200
