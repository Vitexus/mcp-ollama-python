"""
Ollama MCP Server - Main entry point (MCP Python SDK 2.x).
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Use absolute imports so PyInstaller/standalone execution works even when __package__ is not set
try:
    from mcp_ollama_python.server import OllamaMCPServer
    from mcp_ollama_python.ollama_client import OllamaClient
except ImportError:
    from .server import OllamaMCPServer
    from .ollama_client import OllamaClient

try:
    from mcp.server import Server, ServerRequestContext
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequestParams,
        CallToolResult,
        GetPromptRequestParams,
        GetPromptResult,
        ListPromptsResult,
        ListResourcesResult,
        ListToolsResult,
        PaginatedRequestParams,
        Prompt,
        PromptArgument,
        PromptMessage,
        ReadResourceRequestParams,
        ReadResourceResult,
        Resource,
        TextContent,
        TextResourceContents,
        Tool,
    )
except ImportError as e:
    logger.error("MCP package import failed: %s", e)
    print(f"Error: mcp package import failed: {e}")
    print("Please install it with: pip install 'mcp>=2.0.0,<3.0.0'")
    sys.exit(1)


# Global server instance for signal handling
_server_instance: Optional[Server] = None
_shutdown_event: Optional[asyncio.Event] = None


def _package_version() -> str:
    try:
        return version("mcp-ollama-python")
    except PackageNotFoundError:
        return ""


def safe_print(*args, **kwargs) -> None:
    """
    Safe print that handles closed stdout/stderr.

    Args:
        *args: Arguments to print
        **kwargs: Keyword arguments for print function
    """
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        # stdout/stderr is closed, ignore
        pass


def signal_handler(signum: int, frame) -> None:
    """
    Handle shutdown signals gracefully.

    Args:
        signum: Signal number received
        frame: Current stack frame
    """
    # Only perform signal-safe operations - set the shutdown event
    if _shutdown_event:
        _shutdown_event.set()


def _prompt_arguments(raw: Any) -> list[PromptArgument]:
    """Convert server prompt argument dicts to MCP PromptArgument models."""
    if not isinstance(raw, list):
        return []
    out: list[PromptArgument] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not name:
            continue
        out.append(
            PromptArgument(
                name=str(name),
                description=item.get("description"),
                required=bool(item.get("required", False)),
            )
        )
    return out


def _prompt_messages(raw_messages: Any) -> list[PromptMessage]:
    """Convert get_prompt message dicts to MCP PromptMessage models."""
    if not isinstance(raw_messages, list):
        return []
    messages: list[PromptMessage] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role") or "user"
        content = item.get("content") or {}
        text = ""
        if isinstance(content, dict):
            text = str(content.get("text") or "")
        elif isinstance(content, str):
            text = content
        messages.append(
            PromptMessage(role=role, content=TextContent(type="text", text=text))
        )
    return messages


async def main() -> None:
    """
    Main function to start the MCP server.

    Initializes the Ollama client, MCP server, and handles graceful shutdown.
    Registers handlers for tools, resources, and prompts.
    """
    global _server_instance, _shutdown_event

    logger.info("Initializing Ollama MCP Server")

    # Create shutdown event
    _shutdown_event = asyncio.Event()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Ollama client
    try:
        ollama_client = OllamaClient()
        logger.info("Ollama client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Ollama client: %s", e)
        raise

    # Initialize our MCP server
    server = OllamaMCPServer(ollama_client)

    async def handle_list_tools(
        ctx: ServerRequestContext, params: PaginatedRequestParams | None
    ) -> ListToolsResult:
        """Handle list_tools request."""
        del ctx, params  # unused; required by MCP SDK 2 handler signature
        try:
            result = await server.handle_list_tools()
            tools = [
                Tool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    input_schema=tool_data["inputSchema"],
                )
                for tool_data in result["tools"]
            ]
            logger.debug("Listed %d tools", len(tools))
            return ListToolsResult(tools=tools)
        except Exception as e:
            logger.error("Error listing tools: %s", e)
            raise

    async def handle_call_tool(
        ctx: ServerRequestContext, params: CallToolRequestParams
    ) -> CallToolResult:
        """Handle call_tool request."""
        del ctx
        try:
            logger.debug("Calling tool: %s", params.name)
            result = await server.handle_call_tool(params.name, params.arguments or {})

            content = [
                TextContent(type="text", text=item["text"])
                for item in result.get("content") or []
                if item.get("type") == "text" and "text" in item
            ]
            return CallToolResult(
                content=content,
                structured_content=result.get("structuredContent"),
                is_error=bool(result.get("isError", False)),
            )
        except Exception as e:
            logger.error("Error calling tool %s: %s", params.name, e)
            raise

    async def handle_list_resources(
        ctx: ServerRequestContext, params: PaginatedRequestParams | None
    ) -> ListResourcesResult:
        """Handle list_resources request."""
        del ctx, params
        try:
            result = await server.handle_list_resources()
            resources = [
                Resource(
                    uri=resource_data["uri"],
                    name=resource_data["name"],
                    description=resource_data.get("description"),
                    mime_type=resource_data.get("mimeType", "text/plain"),
                )
                for resource_data in result["resources"]
            ]
            logger.debug("Listed %d resources", len(resources))
            return ListResourcesResult(resources=resources)
        except Exception as e:
            logger.error("Error listing resources: %s", e)
            raise

    async def handle_read_resource(
        ctx: ServerRequestContext, params: ReadResourceRequestParams
    ) -> ReadResourceResult:
        """Handle read_resource request."""
        del ctx
        uri = str(params.uri)
        try:
            logger.debug("Reading resource: %s", uri)
            result = await server.handle_read_resource(uri)
            contents: list[TextResourceContents] = []
            for item in result.get("contents") or []:
                contents.append(
                    TextResourceContents(
                        uri=str(item.get("uri") or uri),
                        mime_type=item.get("mimeType", "text/plain"),
                        text=str(item.get("text") or ""),
                    )
                )
            return ReadResourceResult(contents=contents)
        except Exception as e:
            logger.error("Error reading resource %s: %s", uri, e)
            raise

    async def handle_list_prompts(
        ctx: ServerRequestContext, params: PaginatedRequestParams | None
    ) -> ListPromptsResult:
        """Handle list_prompts request."""
        del ctx, params
        try:
            result = await server.handle_list_prompts()
            prompts = [
                Prompt(
                    name=prompt_data["name"],
                    description=prompt_data.get("description"),
                    arguments=_prompt_arguments(prompt_data.get("arguments", [])),
                )
                for prompt_data in result["prompts"]
            ]
            logger.debug("Listed %d prompts", len(prompts))
            return ListPromptsResult(prompts=prompts)
        except Exception as e:
            logger.error("Error listing prompts: %s", e)
            raise

    async def handle_get_prompt(
        ctx: ServerRequestContext, params: GetPromptRequestParams
    ) -> GetPromptResult:
        """Handle get_prompt request."""
        del ctx
        try:
            logger.debug("Getting prompt: %s", params.name)
            result = await server.handle_get_prompt(params.name, params.arguments)
            return GetPromptResult(
                description=result.get("description"),
                messages=_prompt_messages(result.get("messages")),
            )
        except Exception as e:
            logger.error("Error getting prompt %s: %s", params.name, e)
            raise

    # Create MCP server instance (SDK 2: handlers via on_* constructor kwargs)
    mcp_server = Server(
        "ollama-mcp",
        version=_package_version(),
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
        on_list_resources=handle_list_resources,
        on_read_resource=handle_read_resource,
        on_list_prompts=handle_list_prompts,
        on_get_prompt=handle_get_prompt,
    )
    _server_instance = mcp_server

    safe_print("Starting Ollama MCP Server...")
    safe_print("Press Ctrl+C to stop the server")

    # Run the server with graceful shutdown support
    try:
        async with stdio_server() as (read_stream, write_stream):
            safe_print("Server started successfully!")
            safe_print("Waiting for MCP client connections...")

            # Create server task
            server_task = asyncio.create_task(
                mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
            )

            # Wait for either server completion or shutdown signal
            shutdown_task = asyncio.create_task(_shutdown_event.wait())
            done, pending = await asyncio.wait(
                [server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            safe_print("Server stopped.")

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        safe_print("\nServer interrupted by user")
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        safe_print(f"Server error: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Cleaning up resources")
        await ollama_client.client.aclose()
        safe_print("Cleanup completed.")


def run() -> None:
    """
    Entry point for the mcp-ollama-python command.

    Runs the async main function and handles shutdown gracefully.
    """
    try:
        logger.info("Starting mcp-ollama-python")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
        safe_print("\nShutdown complete.")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        safe_print(f"Fatal error: {e}")
        sys.exit(1)


def stop() -> None:
    """
    Stop the running server (for programmatic control).

    Sets the shutdown event to trigger graceful server shutdown.
    """
    if _shutdown_event:
        logger.info("Stop signal sent to server")
        _shutdown_event.set()
        safe_print("Stop signal sent to server")
    else:
        logger.warning("No server instance running")
        safe_print("No server instance running")


if __name__ == "__main__":
    run()
