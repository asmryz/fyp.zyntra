"""
Application settings.

Every value is read from environment variables (loaded from backend/.env).
Secrets such as the database URL, SMTP password and SECRET_KEY are never
hardcoded here.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # Database (the engine itself is created in backend/database.py)
    database_url = os.getenv("DATABASE_URL")

    # Signing key for JWT access tokens and for hashing one-time codes
    secret_key = os.getenv("SECRET_KEY")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Set COOKIE_SECURE=true when the site is served over HTTPS
    cookie_secure = _get_bool("COOKIE_SECURE", False)

    # Frontend address, used for CORS and for links inside emails
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    # SMTP (existing variable names from .env)
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "ZYNTRA")

    # "smtp" sends real emails. "outbox" writes them to backend/dev_outbox/
    # instead, which is only meant for local automated testing.
    email_backend = os.getenv("EMAIL_BACKEND", "smtp").strip().lower()

    # Optional integration points for services that are not part of this
    # web application (LangGraph/RAG assistant and WhatsApp bot)
    ai_service_url = os.getenv("AI_SERVICE_URL", "").strip()
    whatsapp_number = os.getenv("WHATSAPP_NUMBER", "").strip()


settings = Settings()

if not settings.secret_key:
    raise RuntimeError(
        "SECRET_KEY is missing. Add SECRET_KEY to backend/.env "
        "(see backend/.env.example for the format)."
    )
