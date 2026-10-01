"""
Shared HTTP client for all ai_assistant tools.

Maps HTTP status codes back to Python exceptions so tool implementations
don't need to know about HTTP — they just catch ValueError/PermissionError
as before.
"""

import os
import httpx

HR_API_BASE = os.environ.get("HR_API_BASE", "http://localhost:8000")


def call(method: str, path: str, token: str, **kwargs) -> dict:
    """
    Make an authenticated request to the HR API.

    Raises:
        ValueError      on 400 (bad input) or 401 (bad token)
        PermissionError on 403 (not authorized)
        httpx.HTTPError on unexpected server errors
    """
    url = f"{HR_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.request(method, url, headers=headers, **kwargs)

    if response.status_code == 400:
        raise ValueError(response.json()["detail"])
    if response.status_code == 401:
        raise ValueError(response.json()["detail"])
    if response.status_code == 403:
        raise PermissionError(response.json()["detail"])

    response.raise_for_status()
    return response.json()
