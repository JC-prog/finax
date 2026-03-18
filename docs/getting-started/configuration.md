# Configuration

Finax reads all configuration from a `.env` file in the project root. Copy the provided example and fill in your credentials:

```bash
cp .env.example .env
```

---

## Environment Variables

### Google Gemini

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | API key from [Google AI Studio](https://aistudio.google.com/) |

### NewsData.io

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEWSDATA_API_KEY` | Yes | — | API key from [newsdata.io](https://newsdata.io/) |
| `WATCH_TICKERS` | No | `AAPL,TSLA,NVDA,MSFT` | Comma-separated stock tickers to monitor |
| `WATCH_KEYWORDS` | No | `earnings,fed,inflation,rate hike` | Comma-separated keywords to filter articles |

### Telegram

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Yes | Your user ID or group chat ID (use [@userinfobot](https://t.me/userinfobot) to find it) |

### Email (SMTP)

| Variable | Required | Default | Description |
|---|---|---|---|
| `SMTP_HOST` | No | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | No | `587` | SMTP port (STARTTLS) |
| `SMTP_USER` | Yes | — | SMTP username / email address |
| `SMTP_PASSWORD` | Yes | — | SMTP password or App Password |
| `EMAIL_FROM` | Yes | — | Sender address shown in the From header |
| `EMAIL_TO` | Yes | — | Comma-separated list of recipient addresses |

!!! tip "Gmail App Passwords"
    If you use Gmail with 2FA enabled, generate a 16-character App Password at
    **Google Account → Security → 2-Step Verification → App passwords**.
    Use this as `SMTP_PASSWORD` instead of your account password.

### Schedule

| Variable | Required | Default | Description |
|---|---|---|---|
| `SCHEDULE_HOUR` | No | `6` | Hour of day to run (0–23) |
| `SCHEDULE_MINUTE` | No | `0` | Minute of hour to run (0–59) |
| `SCHEDULE_TIMEZONE` | No | `Asia/Singapore` | IANA timezone string |

---

## Example `.env`

```dotenv
GOOGLE_API_KEY=AIzaSy...

NEWSDATA_API_KEY=pub_...
WATCH_TICKERS=AAPL,TSLA,NVDA,MSFT
WATCH_KEYWORDS=earnings,fed,inflation,rate hike

TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=you@gmail.com
EMAIL_TO=you@gmail.com,colleague@example.com

SCHEDULE_HOUR=6
SCHEDULE_MINUTE=0
SCHEDULE_TIMEZONE=Asia/Singapore
```
