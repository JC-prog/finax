import json as _json
from typing import Any

from pydantic import SecretStr
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, DotEnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict


class _CsvFallbackDotEnvSource(DotEnvSettingsSource):
    """DotEnvSettingsSource that falls back to comma-splitting for list fields
    instead of raising SettingsError when the value is not valid JSON."""

    def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:
        if self.field_is_complex(field) and isinstance(value, str):
            try:
                return _json.loads(value)
            except (ValueError, TypeError):
                return [item.strip() for item in value.split(",") if item.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Gemini ---
    google_api_key: SecretStr

    # --- NewsData.io ---
    newsdata_api_key: SecretStr
    watch_tickers: list[str] = ["AAPL", "TSLA", "NVDA", "MSFT"]
    watch_keywords: list[str] = ["earnings", "fed", "inflation"]

    # --- Telegram ---
    telegram_bot_token: SecretStr
    telegram_chat_id: str

    # --- Email (SMTP) ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: SecretStr
    email_from: str
    email_to: list[str]

    # --- Schedule ---
    schedule_hour: int = 6
    schedule_minute: int = 0
    schedule_timezone: str = "Asia/Singapore"

    # --- Logging ---
    log_dir: str = "logs"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, _CsvFallbackDotEnvSource(settings_cls), file_secret_settings)


class _LazySettings:
    """
    Lazy proxy for Settings — defers instantiation until first attribute access.
    This allows importing `settings` at module level without requiring a .env
    file to be present at import time.
    """

    _instance: Settings | None = None

    def _load(self) -> Settings:
        if self._instance is None:
            object.__setattr__(self, "_instance", Settings())
        return self._instance  # type: ignore[return-value]

    def __getattr__(self, name: str):
        return getattr(self._load(), name)


# Module-level singleton — import this everywhere
settings: Settings = _LazySettings()  # type: ignore[assignment]
