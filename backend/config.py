import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Central app configuration, read from environment variables.

    DATABASE_URL supports both MySQL (production, per project spec) and
    SQLite (zero-setup local development). Swap by changing one env var.
    """

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'insightiq.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "60"))
    )
    JWT_TOKEN_LOCATION = ["headers"]

    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173")

    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {"csv", "xlsx"}

    # --- Phase 8: Ask INSIGHT IQ (AI assistant) ---
    # Requires an Anthropic API key: https://console.anthropic.com/settings/keys
    # Without one, the /ask endpoint responds with a clear setup message
    # instead of failing silently or faking an answer.
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "1024"))
    ASK_MAX_HISTORY_MESSAGES = int(os.getenv("ASK_MAX_HISTORY_MESSAGES", "20"))
