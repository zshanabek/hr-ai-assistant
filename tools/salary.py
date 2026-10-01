"""
Salary tool implementation — HTTP client edition.

The >5% VP-approval rule still lives in hr_system/workflows/approval.py.
This file just makes the HTTP call; the enforcement is the server's concern.
"""

from ai_assistant.tools.http_client import call


def request_salary_change(
    session_token: str,
    employee_id: str,
    percentage: float,
    justification: str,
) -> dict:
    return call(
        "POST",
        f"/employees/{employee_id}/salary-changes",
        token=session_token,
        json={"percentage": percentage, "justification": justification},
    )
