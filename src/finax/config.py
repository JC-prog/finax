from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @field_validator("watch_tickers", "watch_keywords", "email_to", mode="before")
    @classmethod
    def split_csv(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


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
