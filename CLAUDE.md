# Project guidance

## Scope and architecture

This is a Python Telegram HR assistant using the Anthropic SDK. Read `README.md`
for setup and runtime requirements.

- `telegram_bot.py` loads `.env`, handles Telegram authentication and messages,
  and persists sessions and conversation history.
- `agent.py` owns the system prompt, tool schemas, dispatcher, and asynchronous
  `run_turn()` loop. Keep AI-specific behavior here so other interfaces can reuse it.
- `tools/` contains thin HTTP adapters. `tools/http_client.py` adds bearer
  authentication and maps API errors to exceptions.
- `data/database.py` owns the assistant's SQLite storage. It is separate from
  the HR system's database.
- The sibling `../hr_system` service owns authorization, business rules,
  approval workflows, and audit records. Do not reproduce or bypass those rules
  in the assistant.

## Runtime assumptions

- Use Python 3.10+ and dependencies listed in `requirements.txt`.
- Run `python telegram_bot.py` from this directory, or
  `python -m ai_assistant.telegram_bot` from its parent directory.
- Imports use the `ai_assistant` package name. Preserve the package layout.
- `agent.py` reads `../hr_system/policies/hr_policies.txt` at import time.
  Importing the agent requires that file to exist.
- Required credentials are `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, and
  `TELEGRAM_BOT_NAME`. `HR_API_BASE` defaults to `http://localhost:8000`.
- The Claude model is configured in `agent.py`, currently `claude-sonnet-4-6`.
- `init_db()` creates `data/ai_assistant.db` on bot startup.

## Making changes

- Follow the existing function-based structure and type annotations. Keep changes
  focused on the requested behavior.
- When adding or changing a tool, keep its schema in `TOOLS`, `_dispatch()` branch,
  and adapter signature consistent with the HR API contract.
- Preserve `run_turn()`'s `(response_text, updated_history)` return value and
  Claude's tool-use/tool-result message pairing.
- Use the authenticated session's identity for HR requests; the server remains
  responsible for checking permissions.
- Keep responses compatible with Telegram Markdown. The current prompt requests
  bullet points and single-asterisk bold labels instead of Markdown tables.
- Database changes must account for existing local databases; `CREATE TABLE IF
  NOT EXISTS` does not migrate existing tables.
- Keep `.env`, credentials, session tokens, chat history, databases, and generated
  files out of commits. Use placeholders in documentation.
- Do not add logging of tokens or complete tool inputs. `_dispatch()` currently
  prints inputs containing tokens; avoid exposing that output in reports.
- Update `README.md` when setup, configuration, commands, or behavior changes.

## Validation

There is no automated test suite or configured formatter/linter in this repository.
For a syntax check from the project directory:

```sh
python -m compileall -q agent.py telegram_bot.py tools data
git diff --check
```

For behavioral changes, use focused checks with mocked Anthropic and HTTP calls,
and a temporary SQLite database rather than the user's session database. Imports
may require the sibling policy file and environment configuration. Do not call
live APIs or submit real HR requests just to validate a code change.

When integration testing is requested, use test accounts and check `/start`,
login, a leave-balance query, conversation persistence, and `/logout`. Report
which checks ran and which external dependencies prevented further validation.
