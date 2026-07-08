import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """
    Try to get a secret from Streamlit's secrets system first,
    then fall back to the .env file.
    This way the same code works locally AND on Streamlit Cloud.
    """
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


class Config:
    GEMINI_API_KEY: str  = _get_secret("GEMINI_API_KEY")
    WHISPER_MODEL: str   = _get_secret("WHISPER_MODEL", "base")
    MAX_AUDIO_MB: int    = int(_get_secret("MAX_AUDIO_SIZE_MB", "50"))
    MAX_AUDIO_BYTES: int = MAX_AUDIO_MB * 1024 * 1024
    DATA_DIR:    str     = "data"
    UPLOADS_DIR: str     = os.path.join("data", "uploads")
    EXPORTS_DIR: str     = os.path.join("data", "exports")
    DB_PATH:     str     = os.path.join("data", "meetings.db")
    APP_ENV:     str     = _get_secret("APP_ENV", "development")
    IS_PROD:     bool    = APP_ENV == "production"

    @classmethod
    def validate(cls) -> list[str]:
        errors = []
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is missing.")
        return errors


config = Config()