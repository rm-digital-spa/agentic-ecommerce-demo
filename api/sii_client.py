"""HTTP client for the sii-mcp service REST routes.

The SII data (companies, invoices) is owned by the sii-mcp component; this
module is the only way the API reads it.
"""

import os

import httpx

SII_MCP_BASE_URL = os.getenv("SII_MCP_BASE_URL", "http://localhost:8001")

_client = httpx.Client(base_url=SII_MCP_BASE_URL, timeout=10.0)


def _get_or_none(path: str) -> dict | None:
    response = _client.get(path)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_sii_companies() -> list[dict]:
    """Get all companies from SII."""
    response = _client.get("/companies")
    response.raise_for_status()
    return response.json()


def get_company_by_rut(rut: str) -> dict | None:
    """Get a company by RUT from SII."""
    return _get_or_none(f"/companies/{rut}")


def get_sii_invoice(invoice_id: str) -> dict | None:
    """Get an invoice from SII by ID."""
    return _get_or_none(f"/invoices/{invoice_id}")


def get_sii_invoice_by_order(order_id: str) -> dict | None:
    """Get an invoice from SII by order ID."""
    return _get_or_none(f"/orders/{order_id}/invoice")
