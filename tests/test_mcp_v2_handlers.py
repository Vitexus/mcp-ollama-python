"""Smoke tests for MCP SDK 2.x handler wiring."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("mcp")

from mcp.server import Server, ServerRequestContext  # noqa: E402
from mcp.types import (  # noqa: E402
    CallToolRequestParams,
    CallToolResult,
    GetPromptRequestParams,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceRequestParams,
    ReadResourceResult,
)


@pytest.mark.asyncio
async def test_sdk2_server_on_handlers_return_typed_results():
    """Low-level Server accepts on_* handlers and returns SDK 2 result types."""
    from mcp_ollama_python import main as main_mod

    backend = MagicMock()
    backend.handle_list_tools = AsyncMock(
        return_value={
            "tools": [
                {
                    "name": "ollama_list",
                    "description": "List models",
                    "inputSchema": {"type": "object", "properties": {}},
                }
            ]
        }
    )
    backend.handle_call_tool = AsyncMock(
        return_value={
            "content": [{"type": "text", "text": '{"ok": true}'}],
            "structuredContent": {"ok": True},
            "isError": False,
        }
    )
    backend.handle_list_resources = AsyncMock(
        return_value={
            "resources": [
                {
                    "uri": "ollama://config",
                    "name": "Config",
                    "description": "cfg",
                    "mimeType": "application/json",
                }
            ]
        }
    )
    backend.handle_read_resource = AsyncMock(
        return_value={
            "contents": [
                {
                    "uri": "ollama://config",
                    "mimeType": "application/json",
                    "text": "{}",
                }
            ]
        }
    )
    backend.handle_list_prompts = AsyncMock(
        return_value={
            "prompts": [
                {
                    "name": "hello_world",
                    "description": "Hello",
                    "arguments": [
                        {
                            "name": "language",
                            "description": "lang",
                            "required": True,
                        }
                    ],
                }
            ]
        }
    )
    backend.handle_get_prompt = AsyncMock(
        return_value={
            "description": "Hello",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": "Write hello world"},
                }
            ],
        }
    )

    async def on_list_tools(ctx, params):
        result = await backend.handle_list_tools()
        from mcp.types import Tool

        return ListToolsResult(
            tools=[
                Tool(
                    name=t["name"],
                    description=t["description"],
                    input_schema=t["inputSchema"],
                )
                for t in result["tools"]
            ]
        )

    async def on_call_tool(ctx, params: CallToolRequestParams):
        result = await backend.handle_call_tool(params.name, params.arguments or {})
        from mcp.types import TextContent

        return CallToolResult(
            content=[
                TextContent(type="text", text=item["text"])
                for item in result.get("content") or []
                if item.get("type") == "text"
            ],
            structured_content=result.get("structuredContent"),
            is_error=bool(result.get("isError", False)),
        )

    async def on_list_resources(ctx, params):
        result = await backend.handle_list_resources()
        from mcp.types import Resource

        return ListResourcesResult(
            resources=[
                Resource(
                    uri=r["uri"],
                    name=r["name"],
                    description=r.get("description"),
                    mime_type=r.get("mimeType", "text/plain"),
                )
                for r in result["resources"]
            ]
        )

    async def on_read_resource(ctx, params: ReadResourceRequestParams):
        result = await backend.handle_read_resource(str(params.uri))
        from mcp.types import TextResourceContents

        return ReadResourceResult(
            contents=[
                TextResourceContents(
                    uri=str(item.get("uri") or params.uri),
                    mime_type=item.get("mimeType", "text/plain"),
                    text=str(item.get("text") or ""),
                )
                for item in result.get("contents") or []
            ]
        )

    async def on_list_prompts(ctx, params):
        result = await backend.handle_list_prompts()
        from mcp.types import Prompt

        return ListPromptsResult(
            prompts=[
                Prompt(
                    name=p["name"],
                    description=p.get("description"),
                    arguments=main_mod._prompt_arguments(p.get("arguments", [])),
                )
                for p in result["prompts"]
            ]
        )

    async def on_get_prompt(ctx, params: GetPromptRequestParams):
        result = await backend.handle_get_prompt(params.name, params.arguments)
        from mcp.types import GetPromptResult

        return GetPromptResult(
            description=result.get("description"),
            messages=main_mod._prompt_messages(result.get("messages")),
        )

    mcp_server = Server(
        "ollama-mcp-test",
        version="test",
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
        on_list_resources=on_list_resources,
        on_read_resource=on_read_resource,
        on_list_prompts=on_list_prompts,
        on_get_prompt=on_get_prompt,
    )
    assert not hasattr(mcp_server, "list_tools") or not callable(
        getattr(type(mcp_server), "list_tools", None)
    )

    ctx = MagicMock(spec=ServerRequestContext)
    tools = await on_list_tools(ctx, None)
    assert isinstance(tools, ListToolsResult)
    assert tools.tools[0].name == "ollama_list"
    assert tools.tools[0].input_schema["type"] == "object"

    call = await on_call_tool(
        ctx, CallToolRequestParams(name="ollama_list", arguments={})
    )
    assert isinstance(call, CallToolResult)
    assert call.content[0].text == '{"ok": true}'
    assert call.structured_content == {"ok": True}
    assert call.is_error is False

    resources = await on_list_resources(ctx, None)
    assert resources.resources[0].mime_type == "application/json"

    read = await on_read_resource(
        ctx, ReadResourceRequestParams(uri="ollama://config")
    )
    assert isinstance(read, ReadResourceResult)
    assert read.contents[0].text == "{}"

    prompts = await on_list_prompts(ctx, None)
    assert prompts.prompts[0].arguments[0].name == "language"
    assert prompts.prompts[0].arguments[0].required is True

    prompt = await on_get_prompt(
        ctx,
        GetPromptRequestParams(name="hello_world", arguments={"language": "Python"}),
    )
    assert prompt.messages[0].content.text == "Write hello world"


def test_prompt_helpers():
    from mcp_ollama_python import main as main_mod

    args = main_mod._prompt_arguments(
        [{"name": "language", "description": "lang", "required": True}, {"skip": True}]
    )
    assert len(args) == 1
    assert args[0].name == "language"

    messages = main_mod._prompt_messages(
        [{"role": "user", "content": {"type": "text", "text": "hi"}}]
    )
    assert messages[0].content.text == "hi"
