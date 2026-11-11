from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[4]
DOTENV_PATH = ROOT_DIR / ".env"
load_dotenv(DOTENV_PATH, override=False)


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "8"))
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    allowed_origins: tuple[str, ...] = _csv(
        os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    )
    gemini_enabled: bool = _bool("GEMINI_ENABLED")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    jev_enabled: bool = _bool("JEV_ENABLED")
    typesafe_api_key: str | None = os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY")
    typesafe_model: str = (
        os.getenv("JEV_MODEL") or os.getenv("TYPESAFE_MODEL") or "jev-latest"
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()

