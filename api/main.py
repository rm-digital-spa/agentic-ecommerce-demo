import logging
import os
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

import db
import seed
from db import ECOMMERCE_DB
from sii_client import (
    get_company_by_rut,
    get_sii_companies,
    get_sii_invoice,
    get_sii_invoice_by_order,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300  # set request timeout to 5 minutes

ECOMMERCE_AGENT_URL = os.getenv("ECOMMERCE_AGENT_URL", "http://localhost:8080")
ECOMMERCE_AGENT_ID = "ecommerce_agent"

seed.seed_data()

security = HTTPBasic()


def verify_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    """Verify HTTP Basic Auth credentials against the api_credential table."""
    if not db.verify_api_credential(credentials.username, credentials.password):
        # logger.info(
        #     f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # logger.info(f"Successful login for username: {credentials.username}")
    return credentials.username


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> db.Customer:
    """Get the current user based on HTTP Basic Auth credentials."""
    if not db.verify_api_credential(credentials.username, credentials.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    user = db.Customer.get_or_none(db.Customer.email == credentials.username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please create an account first.",
        )
    return user


app = FastAPI()
# app = FastAPI(dependencies=[Depends(verify_credentials)])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvokePayload(BaseModel):
    query: str


@app.get("/ping")
def home():
    return {"message": "Hello, World!", "status": "ok"}

# ==================== Auth ====================


class SignupPayload(BaseModel):
    name: str
    email: str
    password: str


@app.post("/auth/users")
def create_user(payload: SignupPayload):
    """Create a new customer account and its API credential (username = email).

    Requires an already-authenticated (e.g. admin) caller.
    """
    name = payload.name.strip()
    email = payload.email.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )

    try:
        customer = db.create_customer_account(name, email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"username": customer["email"], "customer": customer}


@app.get("/auth/users")
def get_users():
    """Return all customer accounts."""
    return db.list_customers()


@app.delete("/auth/users/{customer_id}")
def delete_user(
    customer_id: str,
    username: Annotated[str, Depends(verify_credentials)],
):
    """Delete a customer account, its API credential and chat sessions."""
    customer = db.Customer.get_or_none(db.Customer.id == customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.email == username:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete the account you are signed in with",
        )

    db.delete_customer_account(customer_id)
    return {"message": "Customer deleted successfully"}


# ==================== Sellers (SII Companies) ====================


@app.get("/sellers")
def get_sellers():
    """Return all sellers/companies from SII."""
    return get_sii_companies()


@app.get("/sellers/{rut}")
def get_seller(rut: str):
    """Get a specific seller by RUT."""
    company = get_company_by_rut(rut)
    if not company:
        raise HTTPException(status_code=404, detail="Seller not found")
    return company


# ==================== Products ====================


@app.get("/products")
def get_products():
    """Return all products from the database."""
    products = list(ECOMMERCE_DB["products"].values())
    # Enrich with seller info
    for product in products:
        if product.get("seller_id"):
            seller = get_company_by_rut(product["seller_id"])
            if seller:
                product["seller_name"] = seller["name"]
    return products


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    stock: int | None = None
    sku: str | None = None
    seller_id: str | None = None


class ProductCreate(BaseModel):
    name: str
    price: float
    seller_id: str
    stock: int = 0
    sku: str | None = None


@app.post("/products")
def create_product(product_data: ProductCreate):
    """Create a new product."""
    if not product_data.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    if product_data.price < 0:
        raise HTTPException(status_code=400, detail="Price must be >= 0")
    if product_data.stock < 0:
        raise HTTPException(status_code=400, detail="Stock must be >= 0")

    # Validate seller exists in SII
    if not product_data.seller_id or not product_data.seller_id.strip():
        raise HTTPException(status_code=400, detail="Seller ID (RUT) is required")
    company = get_company_by_rut(product_data.seller_id)
    if not company:
        raise HTTPException(
            status_code=400,
            detail=f"Seller with RUT {product_data.seller_id} not found in SII",
        )

    product_id = f"prod_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    product = {
        "id": product_id,
        "name": product_data.name.strip(),
        "price": float(product_data.price),
        "stock": int(product_data.stock),
        "sku": product_data.sku.strip()
        if product_data.sku and product_data.sku.strip()
        else None,
        "seller_id": product_data.seller_id,
        "created_at": now,
        "updated_at": now,
    }
    ECOMMERCE_DB["products"][product_id] = product
    return product


@app.put("/products/{product_id}")
def update_product(product_id: str, product_data: ProductUpdate):
    if product_id not in ECOMMERCE_DB["products"]:
        raise HTTPException(status_code=404, detail="Product not found")

    product = ECOMMERCE_DB["products"][product_id]

    if product_data.name is not None:
        if not product_data.name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        product["name"] = product_data.name.strip()

    if product_data.price is not None:
        if product_data.price < 0:
            raise HTTPException(status_code=400, detail="Price must be >= 0")
        product["price"] = float(product_data.price)

    if product_data.stock is not None:
        if product_data.stock < 0:
            raise HTTPException(status_code=400, detail="Stock must be >= 0")
        product["stock"] = int(product_data.stock)

    if product_data.sku is not None:
        product["sku"] = product_data.sku if product_data.sku.strip() else None

    if product_data.seller_id is not None:
        if not product_data.seller_id.strip():
            raise HTTPException(status_code=400, detail="Seller ID cannot be empty")
        company = get_company_by_rut(product_data.seller_id)
        if not company:
            raise HTTPException(
                status_code=400,
                detail=f"Seller with RUT {product_data.seller_id} not found in SII",
            )
        product["seller_id"] = product_data.seller_id

    product["updated_at"] = datetime.now(timezone.utc).isoformat()
    ECOMMERCE_DB["products"][product_id] = product

    return product


# ==================== Customers ====================


class CustomerCreate(BaseModel):
    name: str
    email: str


@app.get("/customers")
def get_customers():
    """Return all customers."""
    return list(ECOMMERCE_DB["customers"].values())


@app.post("/customers")
def create_customer(customer_data: CustomerCreate):
    """Create a customer record (no login credential)."""
    if not customer_data.name.strip():
        raise HTTPException(status_code=400, detail="Customer name is required")
    if not customer_data.email.strip() or "@" not in customer_data.email:
        raise HTTPException(status_code=400, detail="A valid email is required")

    normalized_email = customer_data.email.strip().lower()
    for customer in ECOMMERCE_DB["customers"].values():
        if customer["email"] == normalized_email:
            raise HTTPException(
                status_code=409, detail="A customer with this email already exists"
            )

    customer_id = f"cust_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    customer = {
        "id": customer_id,
        "name": customer_data.name.strip(),
        "email": normalized_email,
        "created_at": now,
        "updated_at": now,
    }
    ECOMMERCE_DB["customers"][customer_id] = customer
    return customer


# ==================== Orders ====================


class OrderItem(BaseModel):
    product_id: str
    quantity: int


class OrderCreate(BaseModel):
    customer_id: str
    items: list[OrderItem]


class InvoiceLink(BaseModel):
    invoice_id: str


@app.get("/orders")
def get_orders():
    """Return all orders with invoice status from SII."""
    orders = []
    for order in ECOMMERCE_DB["orders"].values():
        order_copy = order.copy()
        # Fetch invoice from SII if exists
        if order_copy.get("invoice_id"):
            invoice = get_sii_invoice(order_copy["invoice_id"])
            if invoice:
                order_copy["invoice"] = invoice
        orders.append(order_copy)
    return orders


@app.post("/orders")
def create_order(order_data: OrderCreate):
    """Create an order, validating stock and decrementing it atomically."""
    if order_data.customer_id not in ECOMMERCE_DB["customers"]:
        raise HTTPException(status_code=400, detail="Customer not found")
    if not order_data.items:
        raise HTTPException(
            status_code=400, detail="Order must include at least one item"
        )

    order_items: list[dict] = []
    total = 0.0
    # Track seller for invoice (use first item's seller for simplicity)
    primary_seller_id = None

    for item in order_data.items:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Each item must include product_id and quantity > 0",
            )
        if item.product_id not in ECOMMERCE_DB["products"]:
            raise HTTPException(
                status_code=400, detail=f"Product not found: {item.product_id}"
            )

        product = ECOMMERCE_DB["products"][item.product_id]
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product: {item.product_id}",
            )

        if primary_seller_id is None:
            primary_seller_id = product.get("seller_id")

        line_total = product["price"] * item.quantity
        order_items.append(
            {
                "product_id": item.product_id,
                "name": product["name"],
                "unit_price": product["price"],
                "quantity": item.quantity,
                "line_total": line_total,
                "seller_id": product.get("seller_id"),
            }
        )
        total += line_total

    now = datetime.now(timezone.utc).isoformat()
    for item in order_items:
        product = ECOMMERCE_DB["products"][item["product_id"]]
        product["stock"] -= item["quantity"]
        product["updated_at"] = now
        ECOMMERCE_DB["products"][item["product_id"]] = product

    order_id = f"ord_{uuid4().hex[:8]}"
    order = {
        "id": order_id,
        "customer_id": order_data.customer_id,
        "items": order_items,
        "total": round(total, 2),
        "status": "created",
        "invoice_id": None,
        "seller_id": primary_seller_id,  # Include for invoice creation
        "created_at": now,
        "updated_at": now,
    }
    ECOMMERCE_DB["orders"][order_id] = order

    return order


@app.post("/orders/{order_id}/invoice-link")
def link_invoice_to_order(order_id: str, link: InvoiceLink):
    """Link an invoice (created in SII) to an order."""
    if order_id not in ECOMMERCE_DB["orders"]:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ECOMMERCE_DB["orders"][order_id]
    order["invoice_id"] = link.invoice_id
    order["status"] = "invoiced"
    order["updated_at"] = datetime.now(timezone.utc).isoformat()
    ECOMMERCE_DB["orders"][order_id] = order

    return order


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    """Get a specific order with invoice details."""
    if order_id not in ECOMMERCE_DB["orders"]:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ECOMMERCE_DB["orders"][order_id].copy()
    # Fetch invoice from SII if exists
    if order.get("invoice_id"):
        invoice = get_sii_invoice(order["invoice_id"])
        if invoice:
            order["invoice"] = invoice
    return order


# ==================== Invoices (read from SII) ====================


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str):
    """Get an invoice from SII by ID."""
    invoice = get_sii_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@app.get("/orders/{order_id}/invoice")
def get_order_invoice(order_id: str):
    """Get the invoice for a specific order."""
    invoice = get_sii_invoice_by_order(order_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for this order")
    return invoice


# ==================== Chat/Agent ====================


@app.get("/invoke")
def get_invoke():
    return {"message": "Invoke endpoint reached!"}


@app.post("/invoke")
async def post_invoke(
    payload: InvokePayload,
    user_email: Annotated[str | None, Header()] = None,
    session_id: Annotated[str | None, Header()] = None,
):
    """Proxy the query to the ecommerce-agent service, streaming its NDJSON."""
    user = db.Customer.get_or_none(db.Customer.email == user_email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found. Please create an account first.",
        )

    effective_session_id = session_id or user.id

    logger.info(f"User: {user.email}, Session ID: {effective_session_id}")

    db.create_chat_session(
        session_id=effective_session_id,
        agent_id=ECOMMERCE_AGENT_ID,
        user=user,
        chat_label=payload.query,
    )

    agent_payload = {
        "query": payload.query,
        "session_id": effective_session_id,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }

    async def event_generator():
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            async with client.stream(
                "POST", f"{ECOMMERCE_AGENT_URL}/invocations", json=agent_payload
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.error(
                        f"Agent service error {response.status_code}: {body.decode()}"
                    )
                    yield '{"error": "Agent service unavailable"}\n'
                    return
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"

    return StreamingResponse(
        event_generator(),
        media_type="application/x+ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/chat-history")
async def chat_history(
    user: Annotated[db.Customer, Depends(get_current_user)],
):
    """Get chat history for all sessions."""

    sessions = db.list_chat_sessions(user=user)
    return sessions


@app.get("/chat-history/{session_id}")
async def get_chat_history(
    session_id: str, user: Annotated[db.Customer, Depends(get_current_user)]
):
    stored_session = db.get_chat_session(session_id=session_id, user=user)

    if not stored_session:
        raise HTTPException(status_code=404, detail="Session not found")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{ECOMMERCE_AGENT_URL}/sessions/{session_id}/messages",
            params={"agent_id": stored_session["agent_id"]},
        )
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Session not found")
    response.raise_for_status()

    return response.json()


@app.delete("/chat-history/{session_id}")
async def delete_chat_history(
    session_id: str, user: Annotated[db.Customer, Depends(get_current_user)]
):
    """Delete a chat session and its messages."""
    stored_session = db.get_chat_session(session_id=session_id, user=user)

    if not stored_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete the session from the database, then its messages in the agent service
    if db.delete_chat_session(session_id=session_id, user=user):
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.delete(f"{ECOMMERCE_AGENT_URL}/sessions/{session_id}")

    return {"message": "Chat session and its messages deleted successfully."}
