import logging
from typing import Optional
import sys
import os
import json
import uuid
import time

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Add project root to Python path for imports
project_root = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from src.auth.factory import create_auth_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple-tools-server")

user_data_stores = {}


def authenticate_and_save_credentials(user_id):
    """Authenticate with simple-tools service and save API key"""
    logger.info(f"Starting simple-tools authentication for user {user_id}...")

    # Get auth client
    auth_client = create_auth_client()

    # Prompt user for API key if running locally
    api_key = input("Please enter your Simple Tools API key: ").strip()

    if not api_key:
        raise ValueError("API key cannot be empty")

    # Save API key using auth client
    auth_client.save_user_credentials("simple-tools", user_id, {"api_key": api_key})

    logger.info(
        f"Simple Tools API key saved for user {user_id}. You can now run the server."
    )
    return api_key


async def get_simple_tools_credentials(user_id, api_key=None):
    """Get simple-tools API key for the specified user"""
    # Get auth client
    auth_client = create_auth_client(api_key=api_key)

    # Get credentials for this user
    credentials_data = auth_client.get_user_credentials("simple-tools", user_id)

    def handle_missing_credentials():
        error_str = f"Simple Tools API key not found for user {user_id}."
        if os.environ.get("ENVIRONMENT", "local") == "local":
            error_str += " Please run authentication first."
        logger.error(error_str)
        raise ValueError(error_str)

    if not credentials_data:
        handle_missing_credentials()

    api_key = (
        credentials_data.get("api_key")
        if not isinstance(credentials_data, str)
        else credentials_data
    )
    if not api_key:
        handle_missing_credentials()

    return api_key


def create_server(
    user_id: str, api_key: Optional[str] = None, config: Optional[dict] = None
) -> Server:
    """Create a new server instance with optional user context"""
    server = Server("simple-tools-server")

    server.user_id = user_id
    server.api_key = api_key
    server.config = config

    if user_id:
        server.user_id = user_id
        # Initialize user data store if needed
        if user_id not in user_data_stores:
            user_data_stores[user_id] = {}

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """List available prompts"""
        current_user = getattr(server, "user_id", None)
        logger.info(f"Listing prompts for user: {current_user}")

        return [
            types.Prompt(
                name="system",
                description="Sample system prompt",
            ),
        ]

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None = None
    ) -> types.GetPromptResult:
        """Get a specific prompt with arguments"""
        if name == "system":
            content = f"""
Sample system prompt
"""

            return types.GetPromptResult(
                description=f"Sample system prompt",
                messages=[
                    {"role": "user", "content": {"type": "text", "text": content}}
                ],
            )

        raise ValueError(f"Unknown prompt: {name}")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        current_user = getattr(server, "user_id", None)
        logger.info(f"Listing tools for user: {current_user}")

        return [
            types.Tool(
                name="store_data",
                description="Store a key-value pair in the server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["key", "value"],
                },
                outputSchema={
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of JSON strings containing the store operation result",
                    "examples": [
                        '{"id": "store_12345678", "status": "success", "action": "store", "key": "test_key", "value": "test_value", "message": "Stored \'test_key\' with value: test_value", "authenticated": true, "timestamp": 1640995200}'
                    ],
                },
            ),
            types.Tool(
                name="retrieve_data",
                description="Retrieve a value by its key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                    },
                    "required": ["key"],
                },
                outputSchema={
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of JSON strings containing the retrieved value or error message",
                    "examples": [
                        '{"id": "retrieve_87654321", "status": "success", "action": "retrieve", "key": "test_key", "value": "test_value", "message": "Value for \'test_key\': test_value", "timestamp": 1640995260}',
                        '{"id": "retrieve_11223344", "status": "not_found", "action": "retrieve", "key": "nonexistent_key", "message": "Key \'nonexistent_key\' not found", "timestamp": 1640995260}',
                    ],
                },
            ),
            types.Tool(
                name="list_data",
                description="List all stored key-value pairs",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                outputSchema={
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of JSON strings containing all stored key-value pairs or no data message",
                    "examples": [
                        '{"id": "list_55667788", "status": "success", "action": "list", "data": {"test_key": "test_value", "another_key": "another_value"}, "count": 2, "message": "Found 2 items", "formatted_list": "- test_key: test_value\\n- another_key: another_value", "timestamp": 1640995320}',
                        '{"id": "list_99887766", "status": "empty", "action": "list", "data": {}, "count": 0, "message": "No data stored", "timestamp": 1640995320}',
                    ],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        Tools can modify server state and return responses.
        """
        current_user = getattr(server, "user_id", None)
        logger.info(
            f"User {current_user} calling tool: {name} with arguments: {arguments}"
        )

        # Get API key for authentication (demonstrates API key usage)
        try:
            api_key = await get_simple_tools_credentials(
                current_user, api_key=server.api_key
            )
            logger.info(f"Successfully retrieved API key for user {current_user}")
        except ValueError as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Authentication error: {str(e)}",
                )
            ]

        # Get user-specific data store
        data_store = user_data_stores.get(current_user, {})

        if name == "store_data":
            if not arguments:
                raise ValueError("Missing arguments")

            key = arguments.get("key")
            value = arguments.get("value")

            if not key or not value:
                raise ValueError("Missing key or value")

            # Update user-specific server state
            data_store[key] = value
            # Ensure it's saved back to the global store
            if current_user:
                user_data_stores[current_user] = data_store

            result = {
                "id": f"store_{uuid.uuid4().hex[:8]}",
                "status": "success",
                "action": "store",
                "key": key,
                "value": value,
                "message": f"Stored '{key}' with value: {value}",
                "authenticated": True,
                "timestamp": int(time.time()),
            }

            return [types.TextContent(type="text", text=json.dumps(result))]

        elif name == "retrieve_data":
            if not arguments:
                raise ValueError("Missing arguments")

            key = arguments.get("key")

            if not key:
                raise ValueError("Missing key")

            if key not in data_store:
                result = {
                    "id": f"retrieve_{uuid.uuid4().hex[:8]}",
                    "status": "not_found",
                    "action": "retrieve",
                    "key": key,
                    "message": f"Key '{key}' not found",
                    "timestamp": int(time.time()),
                }
            else:
                result = {
                    "id": f"retrieve_{uuid.uuid4().hex[:8]}",
                    "status": "success",
                    "action": "retrieve",
                    "key": key,
                    "value": data_store[key],
                    "message": f"Value for '{key}': {data_store[key]}",
                    "timestamp": int(time.time()),
                }

            return [types.TextContent(type="text", text=json.dumps(result))]

        elif name == "list_data":
            if not data_store:
                result = {
                    "id": f"list_{uuid.uuid4().hex[:8]}",
                    "status": "empty",
                    "action": "list",
                    "data": {},
                    "count": 0,
                    "message": "No data stored",
                    "timestamp": int(time.time()),
                }
            else:
                result = {
                    "id": f"list_{uuid.uuid4().hex[:8]}",
                    "status": "success",
                    "action": "list",
                    "data": data_store,
                    "count": len(data_store),
                    "message": f"Found {len(data_store)} items",
                    "formatted_list": "\n".join(
                        [f"- {k}: {v}" for k, v in data_store.items()]
                    ),
                    "timestamp": int(time.time()),
                }

            return [types.TextContent(type="text", text=json.dumps(result))]

        raise ValueError(f"Unknown tool: {name}")

    return server


server = create_server


def get_initialization_options(server_instance: Server) -> InitializationOptions:
    """Get the initialization options for the server"""
    return InitializationOptions(
        server_name="simple-tools-server",
        server_version="1.0.0",
        capabilities=server_instance.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )


# Main handler allows users to auth
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "auth":
        user_id = "local"
        # Run authentication flow
        authenticate_and_save_credentials(user_id)
    else:
        print("Usage:")
        print("  python main.py auth - Run authentication flow for a user")
        print("Note: To run the server normally, use the guMCP server framework.")
