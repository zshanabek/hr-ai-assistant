"""
Leave tool implementations — HTTP client edition.

Auth, authz, business logic, and audit all happen inside hr_system/server.py.
These functions are thin adapters: they translate Claude tool call arguments
into HTTP requests and return the JSON response.
"""

from ai_assistant.tools.http_client import call


def get_leave_balance(session_token: str, employee_id: str) -> dict:
    return call("GET", f"/employees/{employee_id}/leave-balance", token=session_token)


def submit_leave_request(
    session_token: str,
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
) -> dict:
    return call(
        "POST",
        f"/employees/{employee_id}/leave-requests",
        token=session_token,
        json={"leave_type": leave_type, "start_date": start_date, "end_date": end_date},
    )
