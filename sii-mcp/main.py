import json
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastmcp import FastMCP
from starlette.responses import JSONResponse

# SII data lives inside this component; other services access it via MCP tools
# or the REST routes below — never by reading the file directly.
SHARED_DATA_PATH = os.getenv(
    "SII_DATA_PATH",
    os.path.join(os.path.dirname(__file__), "data", "sii_data.json"),
)

# Invoice status mapping
INVOICE_STATUS = {
    0: "Pending",
    1: "In Progress",
    2: "Completed",
    3: "Failed"
}


def _load_sii_data() -> dict:
    """Load SII data from shared JSON file."""
    with open(SHARED_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_sii_data(data: dict) -> None:
    """Save SII data to shared JSON file."""
    with open(SHARED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


mcp = FastMCP(
    name="sii-mcp",
    instructions="Tool to get information about SII (Servicio de Impuestos Internos). Manages companies/sellers and invoices.",
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "sii-mcp-server"})


# ---- REST routes for service-to-service reads (used by the ecommerce API) ----


def _with_status_label(invoice: dict) -> dict:
    invoice_copy = invoice.copy()
    invoice_copy["status_label"] = INVOICE_STATUS.get(invoice["status"], "Unknown")
    return invoice_copy


@mcp.custom_route("/companies", methods=["GET"])
async def rest_list_companies(request):
    data = _load_sii_data()
    return JSONResponse(data.get("companies", []))


@mcp.custom_route("/companies/{rut}", methods=["GET"])
async def rest_get_company(request):
    rut = request.path_params["rut"]
    data = _load_sii_data()
    for company in data.get("companies", []):
        if company["rut"] == rut:
            return JSONResponse(company)
    return JSONResponse({"detail": "Company not found"}, status_code=404)


@mcp.custom_route("/invoices/{invoice_id}", methods=["GET"])
async def rest_get_invoice(request):
    invoice_id = request.path_params["invoice_id"]
    data = _load_sii_data()
    invoice = data.get("invoices", {}).get(invoice_id)
    if invoice:
        return JSONResponse(_with_status_label(invoice))
    return JSONResponse({"detail": "Invoice not found"}, status_code=404)


@mcp.custom_route("/orders/{order_id}/invoice", methods=["GET"])
async def rest_get_invoice_by_order(request):
    order_id = request.path_params["order_id"]
    data = _load_sii_data()
    for invoice in data.get("invoices", {}).values():
        if invoice["order_id"] == order_id:
            return JSONResponse(_with_status_label(invoice))
    return JSONResponse({"detail": "Invoice not found"}, status_code=404)


@mcp.tool(
    description="""
        Get general information about companies registered in SII. Their RUTs, name and started operations date.
        When asked about "Inicio actividades" return the "started_operations" field.
    """.strip()
)
def get_sii_companies() -> list[dict]:
    """Get all companies registered in SII.

    Returns:
        list: All companies with their RUT, name, started_operations, and giro.
    """
    data = _load_sii_data()
    return data.get("companies", [])


@mcp.tool(
    description="""
        Get information about a specific company by RUT.
    """.strip()
)
def get_company_by_rut(rut: str) -> dict | None:
    """Get a specific company by RUT.

    Args:
        rut: The company RUT (e.g., "76.123.456-7")

    Returns:
        dict: Company information or None if not found.
    """
    data = _load_sii_data()
    for company in data.get("companies", []):
        if company["rut"] == rut:
            return company
    return None


@mcp.tool(
    description="""
        Create a new invoice in SII for an order.
        Returns the created invoice with its ID and status.
        Initial status is 0 (Pending).
    """.strip()
)
def create_invoice(order_id: str, seller_rut: str, total: float) -> dict:
    """Create a new invoice in SII.

    Args:
        order_id: The order ID this invoice is for.
        seller_rut: The RUT of the seller/company.
        total: The total amount of the invoice.

    Returns:
        dict: The created invoice record.
    """
    data = _load_sii_data()

    # Validate seller exists
    seller_exists = any(c["rut"] == seller_rut for c in data.get("companies", []))
    if not seller_exists:
        raise ValueError(f"Company with RUT {seller_rut} not found in SII")

    # Check if invoice already exists for this order
    for invoice in data.get("invoices", {}).values():
        if invoice["order_id"] == order_id:
            return invoice  # Idempotent: return existing invoice

    invoice_id = f"inv_{uuid4().hex[:8]}"
    invoice_number = f"SII-{uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc).isoformat()

    invoice = {
        "id": invoice_id,
        "order_id": order_id,
        "invoice_number": invoice_number,
        "seller_rut": seller_rut,
        "total": round(total, 2),
        "status": 0,  # Pending
        "created_at": now,
    }

    data["invoices"][invoice_id] = invoice
    _save_sii_data(data)

    return invoice


@mcp.tool(
    description="""
        Get an invoice by its ID.
        Returns the invoice with status information.
        Status codes: 0=Pending, 1=In Progress, 2=Completed, 3=Failed
    """.strip()
)
def get_invoice(invoice_id: str) -> dict | None:
    """Get an invoice by ID.

    Args:
        invoice_id: The invoice ID.

    Returns:
        dict: Invoice with status_label added, or None if not found.
    """
    data = _load_sii_data()
    invoice = data.get("invoices", {}).get(invoice_id)
    if invoice:
        invoice_copy = invoice.copy()
        invoice_copy["status_label"] = INVOICE_STATUS.get(invoice["status"], "Unknown")
        return invoice_copy
    return None


@mcp.tool(
    description="""
        Get an invoice by order ID.
        Returns the invoice associated with the given order.
    """.strip()
)
def get_invoice_by_order(order_id: str) -> dict | None:
    """Get an invoice by order ID.

    Args:
        order_id: The order ID.

    Returns:
        dict: Invoice with status_label added, or None if not found.
    """
    data = _load_sii_data()
    for invoice in data.get("invoices", {}).values():
        if invoice["order_id"] == order_id:
            invoice_copy = invoice.copy()
            invoice_copy["status_label"] = INVOICE_STATUS.get(invoice["status"], "Unknown")
            return invoice_copy
    return None


@mcp.tool(
    description="""
        Update the status of an invoice.
        Valid statuses: 0=Pending, 1=In Progress, 2=Completed, 3=Failed
    """.strip()
)
def update_invoice_status(invoice_id: str, status: int) -> dict:
    """Update an invoice's status.

    Args:
        invoice_id: The invoice ID.
        status: New status (0=Pending, 1=In Progress, 2=Completed, 3=Failed)

    Returns:
        dict: Updated invoice record.
    """
    if status not in INVOICE_STATUS:
        raise ValueError(f"Invalid status {status}. Must be 0, 1, 2, or 3.")

    data = _load_sii_data()

    if invoice_id not in data.get("invoices", {}):
        raise ValueError(f"Invoice {invoice_id} not found")

    data["invoices"][invoice_id]["status"] = status
    _save_sii_data(data)

    invoice = data["invoices"][invoice_id].copy()
    invoice["status_label"] = INVOICE_STATUS[status]
    return invoice


@mcp.tool(
    description="""
        List all invoices in SII.
        Returns all invoices with their status information.
    """.strip()
)
def list_invoices() -> list[dict]:
    """List all invoices.

    Returns:
        list: All invoices with status_label added.
    """
    data = _load_sii_data()
    invoices = []
    for invoice in data.get("invoices", {}).values():
        invoice_copy = invoice.copy()
        invoice_copy["status_label"] = INVOICE_STATUS.get(invoice["status"], "Unknown")
        invoices.append(invoice_copy)
    return invoices


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("SII_MCP_PORT", 8000)),
    )
