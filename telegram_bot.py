"""
HR Assistant — Telegram bot.

Auth flow (OAuth-style via Telegram deep link):
  1. User sends /start
  2. Bot generates a one-time state token → sends HR login link
  3. User logs in on the HR system (picks their account)
  4. HR system redirects to t.me/<BOT_NAME>?start=<state>
  5. Telegram sends /start <state> to the bot
  6. Bot exchanges state for session_token via GET /auth/telegram/token
  7. chat_id → session_token stored; user can chat freely

Env vars required:
  TELEGRAM_BOT_TOKEN   — from @BotFather
  TELEGRAM_BOT_NAME    — your bot's username without @  (e.g. my_hr_bot)
  HR_API_BASE          — HR system URL (default: http://localhost:8000)

Run:
  python -m ai_assistant.telegram_bot
"""

import logging
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import httpx
from ai_assistant.agent import run_turn
from ai_assistant.data.database import (
    init_db, get_session, save_session, delete_session,
    get_history, save_history,
)
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
BOT_NAME   = os.environ["TELEGRAM_BOT_NAME"]
HR_API_BASE = os.environ.get("HR_API_BASE", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Per-chat state is persisted in ai_assistant/data/ai_assistant.db



# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        # Step 1 — generate state, send login link
        state = secrets.token_urlsafe(16)
        login_url = f"{HR_API_BASE}/auth/telegram/login?state={state}&bot_name={BOT_NAME}"
        await update.message.reply_text(
            f"Welcome to the HR Assistant!\n\nPlease log in to continue:\n{login_url}"
        )
        return

    # Step 5 — exchange state for session_token
    state = args[0]
    try:
        resp = httpx.get(f"{HR_API_BASE}/auth/telegram/token?state={state}", timeout=10)
        if resp.status_code == 200:
            session_token = resp.json()["session_token"]
            me_resp = httpx.get(
                f"{HR_API_BASE}/me",
                headers={"Authorization": f"Bearer {session_token}"},
                timeout=10,
            )
            employee_id = me_resp.json().get("employee_id") if me_resp.status_code == 200 else None
            save_session(chat_id, session_token, employee_id)
            save_history(chat_id, [])
            await update.message.reply_text(
                "You're logged in! How can I help you?\n\n"
                "Try: *What's my leave balance?* or *What is the parental leave policy?*",
                parse_mode="Markdown",
            )
        elif resp.status_code == 410:
            await update.message.reply_text("Login link expired. Send /start to get a new one.")
        else:
            await update.message.reply_text("Login failed. Send /start to try again.")
    except httpx.RequestError:
        await update.message.reply_text("Could not reach HR system. Please try again later.")


async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    delete_session(chat_id)
    await update.message.reply_text("Logged out. Send /start to log in again.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    session_token, employee_id = get_session(chat_id)

    if not session_token:
        await update.message.reply_text("Please log in first — send /start")
        return

    # Show typing indicator while waiting for Claude
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        history = get_history(chat_id)
        response_text, updated_history = await run_turn(
            user_message=update.message.text,
            session_token=session_token,
            employee_id=employee_id,
            history=history,
        )
        save_history(chat_id, updated_history)
        await update.message.reply_text(response_text, parse_mode="Markdown")
    except Exception as e:
        log.exception("Error in agentic loop")
        await update.message.reply_text(f"Something went wrong: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("logout", cmd_logout))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
