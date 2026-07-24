# Import the Agent class from the strands package
# The Agent class provides AI capabilities for question answering and other tasks
import os
from strands import Agent
from strands.models import BedrockModel
from strands.tools import tool
from strands.tools.mcp import MCPClient
from strands.multiagent.a2a import A2AServer
from mcp.client.streamable_http import streamable_http_client
from langfuse import get_client
import uvicorn
from common.agenthooks import NamedAgentHook



MCP_URL = os.getenv("SII_MCP_URL", "http://localhost:8001/mcp")
AGENT_PORT = int(os.getenv("SII_AGENT_PORT", 8002))
HOST = os.getenv("HOST", "0.0.0.0")

# Verify connection
langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")


@tool
def sii_status_translator(status_code: int) -> str:
    """Translate SII status codes to human-readable status.
    Args:
        status_code (int): The SII status code to translate.
    Returns:
        str: The human-readable status corresponding to the status code.
    """
    print(f"Translating SII status code: {status_code} {type(status_code)}")
    status_dict = {0: "Pending", 1: "In Progress", 2: "Completed", 3: "Failed"}
    return status_dict.get(status_code, "Unknown Status")


model = BedrockModel(
    region_name="us-east-1",
    model_id= os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0"),
    max_tokens=4096,
)
sii_mcp = MCPClient(lambda: streamable_http_client(MCP_URL))


with sii_mcp:
    mcp_tools = sii_mcp.list_tools_sync()

    print("Available tools from MCP:", mcp_tools)

    agent = Agent(
        description="An assistant for the Chilean Internal Revenue Service (SII) to help users manage invoices and provide general information about companies registered in SII.",
        system_prompt="""
        You are an assistant for the Chilean Internal Revenue Service (SII).
        Your main functions are:
        1. Create invoices for orders - use the create_invoice tool with order_id, seller_rut, and total
        2. Check invoice status - use get_invoice or get_invoice_by_order tools
        3. Update invoice status - use update_invoice_status tool
        4. List all invoices - use list_invoices tool
        5. Get company information - use get_sii_companies or get_company_by_rut tools

        When asked to create an invoice, always use the create_invoice tool from MCP.
        Always use the tools when relevant to provide accurate and up-to-date information.
        Return the invoice details after creating or retrieving them.
        """,
        model=model,
        tools=mcp_tools + [sii_status_translator],
        hooks=[NamedAgentHook("SII Agent")],
    )
    print("SII Agent initialized using model:", agent.model.config)

    a2a_server = A2AServer(agent=agent, port=AGENT_PORT)

    app = a2a_server.to_fastapi_app()

    app.get("/health")(lambda: {"status": "healthy", "service": "sii-agent"})

    uvicorn.run(app, host=HOST, port=AGENT_PORT)
