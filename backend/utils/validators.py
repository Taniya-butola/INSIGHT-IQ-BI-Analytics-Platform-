import re
from email_validator import validate_email, EmailNotValidError

PASSWORD_MIN_LEN = 8
_PASSWORD_RULES = [
    (re.compile(r"[A-Z]"), "one uppercase letter"),
    (re.compile(r"[a-z]"), "one lowercase letter"),
    (re.compile(r"[0-9]"), "one number"),
]


def validate_registration_payload(data: dict) -> list[str]:
    """Returns a list of human-readable error strings; empty list means valid."""
    errors = []

    full_name = (data.get("full_name") or "").strip()
    if len(full_name) < 2:
        errors.append("Full name must be at least 2 characters.")

    email = (data.get("email") or "").strip()
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        errors.append("Enter a valid email address.")

    password = data.get("password") or ""
    if len(password) < PASSWORD_MIN_LEN:
        errors.append(f"Password must be at least {PASSWORD_MIN_LEN} characters.")
    for pattern, description in _PASSWORD_RULES:
        if not pattern.search(password):
            errors.append(f"Password must contain at least {description}.")

    return errors


def validate_login_payload(data: dict) -> list[str]:
    errors = []
    if not (data.get("email") or "").strip():
        errors.append("Email is required.")
    if not (data.get("password") or ""):
        errors.append("Password is required.")
    return errors


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
