"""HTTP client for the ecommerce API.

The agent no longer touches SQLite directly: every data operation goes through
the API's REST endpoints, which own validation and stock logic.
"""

import os
from typing import Any

import httpx

ECOMMERCE_API_URL = os.getenv("ECOMMERCE_API_URL", "http://localhost:8000")
ECOMMERCE_API_USERNAME = os.getenv("ECOMMERCE_API_USERNAME", "admin")
ECOMMERCE_API_PASSWORD = os.getenv("ECOMMERCE_API_PASSWORD", "admin123")

_client = httpx.Client(
    base_url=ECOMMERCE_API_URL,
    auth=(ECOMMERCE_API_USERNAME, ECOMMERCE_API_PASSWORD),
    timeout=30.0,
)


def _raise_for_detail(response: httpx.Response) -> None:
    """Convert API validation errors into ValueError so the agent can read them."""
    if response.is_success:
        return
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    raise ValueError(str(detail))


def get(path: str, params: dict[str, Any] | None = None) -> Any:
    response = _client.get(path, params=params)
    _raise_for_detail(response)
    return response.json()


def post(path: str, payload: dict[str, Any]) -> Any:
    response = _client.post(path, json=payload)
    _raise_for_detail(response)
    return response.json()
