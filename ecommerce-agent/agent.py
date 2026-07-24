"""Ecommerce agent definition.

Extracted from the API service so it can be deployed on its own (AWS AgentCore
Runtime). Tools operate on the ecommerce API over HTTP; SII operations go
through the sii_assistant tool injected by main.py.
"""

import os
from typing import Any

from common.agenthooks import NamedAgentHook
from strands import Agent
from strands.memory import MemoryManager
from strands.models import BedrockModel
from strands.session import FileSessionManager
from strands.tools import tool
from strands.vended_memory_stores.bedrock_knowledge_base import (
    BedrockKnowledgeBaseStore,
)

import api_client

model = BedrockModel(
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0"),
    max_tokens=4096,
)

# Bedrock Knowledge Base used as the user-preferences memory store.
# The data source must be of type CUSTOM to allow direct writes (add).
BEDROCK_KB_ID = os.getenv("BEDROCK_KB_ID", "")
BEDROCK_KB_DATA_SOURCE_ID = os.getenv("BEDROCK_KB_DATA_SOURCE_ID", "")
BEDROCK_KB_S3_BUCKET = os.getenv("BEDROCK_KB_S3_BUCKET", "")
BEDROCK_KB_S3_PREFIX = os.getenv("BEDROCK_KB_S3_PREFIX", "memories/")

# Session state directory (ephemeral inside a container; future: AgentCore Memory)
SESSIONS_DIR = os.getenv(
    "SESSIONS_DIR", os.path.join(os.path.dirname(__file__), "sessions")
)
os.makedirs(SESSIONS_DIR, exist_ok=True)


# Product Tools
@tool
def create_product(
    name: str, price: float, seller_id: str, stock: int = 0, sku: str | None = None
) -> dict[str, Any]:
    """Create a product in the ecommerce catalog.

    Use this tool to register a new sellable product.

    Args:
        name: Product display name. Must be a non-empty string.
        price: Product unit price. Must be a number >= 0.
        seller_id: The RUT of the seller company (must exist in SII).
        stock: Initial stock quantity. Must be an integer >= 0.
        sku: Optional stock keeping unit identifier.

    Returns:
        The created product record.
    """
    return api_client.post(
        "/products",
        {"name": name, "price": price, "seller_id": seller_id, "stock": stock, "sku": sku},
    )


@tool
def list_products() -> list[dict[str, Any]]:
    """Return all products currently stored in the ecommerce catalog."""
    return api_client.get("/products")


@tool
def show_products(filter_ids: list[str]) -> list[dict[str, Any]]:
    """Display products to the user as visual cards, selected by product ID.

    This is the ONLY tool whose output is rendered as product cards in the
    chat UI. Call it after list_products with the ids you want the user to
    see: all ids to show the full catalog, or a subset for recommendations.

    Args:
        filter_ids: Product IDs to display (e.g. ["prod_phone001"]).

    Returns:
        Full product records for the ids that exist, in catalog order.
    """
    products = api_client.get("/products")
    wanted = set(filter_ids)
    return [p for p in products if p["id"] in wanted]


@tool
def list_sellers() -> list[dict[str, Any]]:
    """Return all sellers/companies registered in SII.

    Use this to get valid seller_id values for creating products.

    Returns:
        List of companies with their RUT, name, and giro.
    """
    return api_client.get("/sellers")


# Customer Tools
@tool
def create_customer(name: str, email: str) -> dict[str, Any]:
    """Create a customer in the ecommerce database.

    Args:
        name: Customer full name. Must be a non-empty string.
        email: Customer email. Must contain '@' and be unique.

    Returns:
        The created customer record.
    """
    return api_client.post("/customers", {"name": name, "email": email})


@tool
def list_customers() -> list[dict[str, Any]]:
    """Return all customers currently stored in the ecommerce database."""
    return api_client.get("/customers")


# Order tools
@tool
def create_order(customer_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Create an order. After creating, you MUST use sii_assistant to create an invoice.

    IMPORTANT: This tool only creates the order. You must then:
    1. Call sii_assistant with: "Create invoice for order {order_id} with seller_rut {seller_id} and total {total}"
    2. Call link_invoice_to_order to link the invoice to the order

    Args:
        customer_id: Existing customer ID.
        items: Non-empty list of objects with keys:
            - product_id: Existing product ID
            - quantity: Integer > 0

    Returns:
        The created order record with seller_id for invoice creation.
    """
    return api_client.post("/orders", {"customer_id": customer_id, "items": items})


@tool
def link_invoice_to_order(order_id: str, invoice_id: str) -> dict[str, Any]:
    """Link an invoice (created via sii_assistant) to an order.

    Call this after using sii_assistant to create the invoice.

    Args:
        order_id: The order ID to link.
        invoice_id: The invoice ID returned by sii_assistant.

    Returns:
        The updated order with invoice linked.
    """
    return api_client.post(
        f"/orders/{order_id}/invoice-link", {"invoice_id": invoice_id}
    )


@tool
def list_orders() -> list[dict[str, Any]]:
    """Return all orders currently stored in the ecommerce database."""
    return api_client.get("/orders")


@tool
def get_order_with_invoice(order_id: str) -> dict[str, Any]:
    """Get an order with its invoice details from SII.

    Args:
        order_id: The order ID.

    Returns:
        Order with invoice details including current status.
    """
    return api_client.get(f"/orders/{order_id}")


ECOMMERCE_SYSTEM_PROMPT = """
                You are an ecommerce operations agent for products, customers, orders, and invoices.

                Core behavior:
                - Always validate user input before calling any tool.
                - Never invent IDs, prices, stock, emails, or invoice numbers.
                - If required fields are missing or invalid, ask a concise follow-up question instead of calling a tool.
                - Prefer safe read-first behavior when user intent is ambiguous.

                Validation policy:
                - create_product: require non-empty name, price >= 0, stock integer >= 0, and valid seller_id (RUT).
                    Use list_sellers to get valid seller RUTs if needed.
                - create_customer: require non-empty name and valid email containing @.
                - create_order: require existing customer_id and non-empty items list.
                    Each item must include existing product_id and integer quantity > 0 with sufficient stock.

                IMPORTANT - Order Creation Workflow:
                When creating an order, you MUST follow these steps:
                1. Call get_current_customer to confirm the authenticated customer.
                2. Call create_order to create the order (returns order with id, total, and seller_id)
                3. Call sii_assistant to create the invoice: "Create invoice for order {order_id} with seller_rut {seller_id} and total {total}"
                4. Extract the invoice_id from the sii_assistant response
                5. Call link_invoice_to_order with the order_id and invoice_id

                Do NOT skip the sii_assistant step - invoices must be created through SII.

                Execution policy:
                - Use only the minimum necessary tool calls to complete the request.
                - On tool validation errors, explain the exact field that failed and how to fix it.
                - Keep responses concise and action-oriented.

                Output style:
                - For successful writes, return a short confirmation and key IDs.
                - For reads, summarize the most relevant records clearly.
                - When showing order details, include invoice status from SII.

                UI rendering (IMPORTANT):
                - list_products is an INTERNAL data tool: its output is NEVER shown
                  to the user. Use it only to read the catalog for yourself.
                - show_products is the ONLY way products appear on the
                  user's screen: the chat UI renders its result as visual product
                  cards (name, price, stock, SKU).
                - Whenever the user should SEE products, you MUST end with a
                  show_products call containing the ids to display:
                    * "show/list all products" -> call list_products, then call
                      show_products with ALL the ids from it.
                    * suggestions, search, or category questions -> call
                      list_products, then call show_products with ONLY
                      the relevant ids.
                - The user sees the cards the moment show_products
                  returns. NEVER repeat, enumerate, or summarize those products
                  in your text response. No bullet lists, no tables, no names or
                  prices.
                - Instead, reply with a single short sentence, e.g. a count and an
                  offer to help ("Here are the 20 products in the catalog — want
                  details on any of them?").
                - Exception: when giving purchase advice or comparisons, you may
                  name the specific products you recommend and why — but still do
                  not re-list the full catalog.

                --- PURCHASE ADVICE ---

                You also act as a shopping advisor. When the user asks for advice,
                recommendations, suggestions, gift ideas, comparisons, or "what should
                I buy" style questions:

                1. Call get_current_customer to identify the authenticated customer.
                2. Call list_products to get the real catalog (names, prices, stock).
                3. Call list_orders and filter by the customer's id to learn their
                   preferences from past purchases (product types, brands, price range).
                4. From the list_products result, select the ids of ONLY the products
                   relevant to the user's request (their stated interest, category,
                   budget, or purchase history). Include products directly related to
                   the request and close complements (e.g. for "basketball": the
                   basketball itself and sport shoes, but not a printer).
                5. Call show_products with those selected ids. This is the
                   only step that shows the user the recommended products as
                   cards — do NOT skip it, and never pass all the ids here when
                   the user asked for a suggestion.
                6. Recommend ONLY products that exist in the catalog and have stock > 0.
                   Use exact stored names and prices — never invent or estimate them.
                7. If NO catalog product matches the request, do not call
                   show_products with unrelated ids — say briefly that
                   nothing in the catalog matches and ask about other interests.

                Advice rules:
                - Personalize when history exists: relate suggestions to what the
                  customer bought before (e.g. complements, upgrades, same category).
                - If the customer has no order history, ask briefly about their
                  interests or budget, or recommend popular/varied catalog items.
                - Respect any budget the user states; suggest the best options within it.
                - When comparing products, use only stored attributes (price, stock,
                  seller) plus general product knowledge, and say which you'd pick and why.
                - Mention stock only when it is low (e.g. fewer than 5 units) as a
                  purchase consideration.
                - Giving advice is read-only: do NOT create an order unless the user
                  explicitly asks to buy. After advising, you may offer to place the
                  order, and if accepted, follow the full Order Creation Workflow above.
        """


def get_session(session_id: str) -> FileSessionManager:
    return FileSessionManager(
        storage_dir=SESSIONS_DIR,
        session_id=session_id,
    )


def build_ecommerce_agent(
    tools: list, session_id: str, user: dict[str, str]
) -> Agent:
    """Build the agent for one invocation.

    Args:
        tools: Extra tools to attach (e.g. sii_assistant).
        session_id: Conversation session id (FileSessionManager key).
        user: Authenticated customer as {"id", "name", "email"}.
    """

    @tool
    def get_current_customer() -> dict[str, Any]:
        """Return the current authenticated customer."""
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        }

    native_tools = [
        create_product,
        list_products,
        show_products,
        list_sellers,
        create_customer,
        list_customers,
        create_order,
        link_invoice_to_order,
        list_orders,
        get_order_with_invoice,
        get_current_customer,
    ]

    all_tools = native_tools + tools

    session_mgr = None
    if session_id:
        session_mgr = get_session(session_id)

    memory_manager = None
    if BEDROCK_KB_ID:
        user_preference_store = BedrockKnowledgeBaseStore(
            name="user_preferences",
            description="Long-term user preferences (theme, favorite categories, budget, etc.)",
            config={
                "knowledge_base_id": BEDROCK_KB_ID,
                "data_source_type": "S3",
                "data_source_id": BEDROCK_KB_DATA_SOURCE_ID,
                "s3": {"bucket": BEDROCK_KB_S3_BUCKET, "prefix": BEDROCK_KB_S3_PREFIX},
            },
            # Isolates each customer's memories via the KB metadata filter
            scope=f"user-{user['id']}",
            writable=True,
        )
        memory_manager = MemoryManager(
            stores=[user_preference_store],
            add_tool_config=True,
        )

    return Agent(
        agent_id="ecommerce_agent",
        system_prompt=ECOMMERCE_SYSTEM_PROMPT,
        model=model,
        tools=all_tools,
        hooks=[NamedAgentHook("EcommerceAgent")],
        memory_manager=memory_manager,
        session_manager=session_mgr,
    )
