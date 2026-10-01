"""
HR Assistant — agentic loop.

Single place for the system prompt, tool schemas, tool dispatcher,
and the Claude conversation loop. Any interface (Telegram, web, CLI)
imports run_turn() and stays free of AI-specific details.
"""

import json
from pathlib import Path

from anthropic import AsyncAnthropic

_POLICY_TEXT = (
    Path(__file__).parent.parent / "hr_system" / "policies" / "hr_policies.txt"
).read_text()

SYSTEM_PROMPT = """You are an internal HR assistant for ACME Corp.
You help employees with HR policies, leave balances, leave requests, and salary changes.
Be professional and concise.
When calling tools, always use the session_token provided to you.
Format responses for Telegram: use bullet points instead of tables, bold labels with *, no markdown tables.

== HR POLICY REFERENCE ==
""" + _POLICY_TEXT

TOOLS = [
    {
        "name": "get_leave_balance",
        "description": "Retrieve remaining leave days for an employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_token": {"type": "string"},
                "employee_id":   {"type": "string"},
            },
            "required": ["session_token", "employee_id"],
        },
    },
    {
        "name": "submit_leave_request",
        "description": "Submit a leave request. Employees may only submit for themselves.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_token": {"type": "string"},
                "employee_id":   {"type": "string"},
                "leave_type":    {"type": "string", "enum": ["vacation", "sick", "parental"]},
                "start_date":    {"type": "string", "description": "YYYY-MM-DD"},
                "end_date":      {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["session_token", "employee_id", "leave_type", "start_date", "end_date"],
        },
    },
    {
        "name": "request_salary_change",
        "description": "Request a salary increase for a direct report (managers only).",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_token": {"type": "string"},
                "employee_id":   {"type": "string"},
                "percentage":    {"type": "number"},
                "justification": {"type": "string"},
            },
            "required": ["session_token", "employee_id", "percentage", "justification"],
        },
    },
]


def _dispatch(tool_name: str, tool_input: dict) -> str:
    print(f"Dispatching tool: {tool_name} with input: {tool_input}")
    from ai_assistant.tools.leave import get_leave_balance, submit_leave_request
    from ai_assistant.tools.salary import request_salary_change
    try:
        if tool_name == "get_leave_balance":
            result = get_leave_balance(**tool_input)
        elif tool_name == "submit_leave_request":
            result = submit_leave_request(**tool_input)
        elif tool_name == "request_salary_change":
            result = request_salary_change(**tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
    except (ValueError, PermissionError) as e:
        result = {"error": str(e)}
    return json.dumps(result)


async def run_turn(
    user_message: str,
    session_token: str,
    history: list[dict],
    employee_id: str | None = None,
) -> tuple[str, list[dict]]:
    """
    Run one user turn through the agentic loop.

    Returns (response_text, updated_history).
    """
    client = AsyncAnthropic()
    system = SYSTEM_PROMPT + f"\n\nThe current user's session token is: {session_token}"
    if employee_id:
        system += f"\nThe current user's employee ID is: {employee_id}. Use this automatically when tools require an employee_id — never ask the user for it."
    messages = history + [{"role": "user", "content": user_message}]

    while True:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        serialized = [block.model_dump() for block in response.content]
        messages.append({"role": "assistant", "content": serialized})

        if response.stop_reason == "end_turn":
            text = " ".join(b.text for b in response.content if b.type == "text")
            return text, messages

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                result_str = _dispatch(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })
            messages.append({"role": "user", "content": tool_results})
