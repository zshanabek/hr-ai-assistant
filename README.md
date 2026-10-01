# HR AI Assistant

A Claude-powered Telegram bot for HR policy questions, leave balances, leave
requests, and manager salary-change requests. The companion HR API handles
permissions and business rules; SQLite stores sessions and chat history.

## Setup

Requires Python 3.10+, an Anthropic API key, a Telegram bot, and the companion
`hr_system` directory alongside this project, including `policies/hr_policies.txt`.

From `ai_assistant`:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```dotenv
ANTHROPIC_API_KEY=your_api_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_NAME=your_bot_username_without_at
HR_API_BASE=http://localhost:8000
```

## Run

Start the companion HR API, then run from `ai_assistant`:

```sh
python telegram_bot.py
```

In Telegram, send `/start` and follow the login link. Ask an HR question or request
leave. Send `/logout` to clear your session and history.

The HR API URL must be reachable by both the bot and your login browser.
See [CLAUDE.md](CLAUDE.md) for development guidance.
