# Configuration Reference

**File:** `src/finax/config.py`

Finax uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load and validate all configuration from the `.env` file.

---

## Settings class

```python
class Settings(BaseSettings):
    # Google Gemini
    google_api_key: str

    # NewsData.io
    newsdata_api_key: str
    watch_tickers:   list[str]   = ["AAPL", "TSLA", "NVDA", "MSFT"]
    watch_keywords:  list[str]   = ["earnings", "fed", "inflation", "rate hike"]

    # Telegram
    telegram_bot_token: str
    telegram_chat_id:   str

    # SMTP
    smtp_host:     str = "smtp.gmail.com"
    smtp_port:     int = 587
    smtp_user:     str
    smtp_password: str
    email_from:    str
    email_to:      list[str]

    # Schedule
    schedule_hour:     int = 6
    schedule_minute:   int = 0
    schedule_timezone: str = "Asia/Singapore"

    model_config = SettingsConfigDict(env_file=".env")
```

---

## Lazy loading

Settings are accessed through a module-level proxy object that defers `.env` parsing until first attribute access. This means importing `finax` modules in tests or scripts does not require a `.env` file to be present.

```python
# config.py
from functools import cached_property

class _SettingsProxy:
    @cached_property
    def _settings(self) -> Settings:
        return Settings()

    def __getattr__(self, name: str):
        return getattr(self._settings, name)

settings = _SettingsProxy()
```

---

## Accessing settings

Import the `settings` proxy anywhere in the codebase:

```python
from finax.config import settings

api_key = settings.google_api_key
tickers = settings.watch_tickers
```
