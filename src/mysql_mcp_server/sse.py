import logging
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

from .server import app as mcp_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mysql_mcp_server_sse")

# Create SSE transport targeting the /messages endpoint
sse = SseServerTransport("/messages")

async def handle_sse(request):
    """Handle the initial GET request to establish the SSE connection."""
    logger.info("Client connected to SSE endpoint")
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        logger.info("Initializing MCP server over SSE")
        try:
            await mcp_app.run(
                streams[0], streams[1], mcp_app.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"Error during SSE connection running app: {e}", exc_info=True)

async def handle_messages(request):
    """Handle incoming POST requests containing MCP messages."""
    await sse.handle_post_message(
        request.scope, request.receive, request._send
    )

# Create Starlette app
api = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)
