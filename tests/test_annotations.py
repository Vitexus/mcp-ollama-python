"""MCP-SERVER-STANDARDS section 7: annotations, naming consistency, read-only mode."""

import json
import pathlib

import pytest

from mcp_server_ollama.autoloader import discover_tools_with_handlers

ROOT = pathlib.Path(__file__).parent.parent
ALL_TOOLS = {
    "ollama_list", "ollama_ps", "ollama_show", "ollama_generate", "ollama_chat",
    "ollama_embed", "ollama_pull", "ollama_delete", "ollama_execute",
}


@pytest.fixture
def all_tools(monkeypatch):
    monkeypatch.setenv("OLLAMA_EXECUTE_ENABLED", "1")
    monkeypatch.delenv("OLLAMA_READ_ONLY", raising=False)


async def test_every_tool_has_title_and_four_hints(all_tools):
    tools = (await discover_tools_with_handlers()).tools
    assert {t.name for t in tools} == ALL_TOOLS
    for t in tools:
        a = t.annotations
        assert t.title and t.title != t.name, t.name
        assert a is not None, t.name
        for hint in ("read_only_hint", "destructive_hint", "idempotent_hint", "open_world_hint"):
            assert getattr(a, hint) is not None, (t.name, hint)
        assert not (a.read_only_hint and a.destructive_hint), t.name


async def test_name_consistency(all_tools):
    for t in (await discover_tools_with_handlers()).tools:
        if any(w in t.name for w in ("_list", "_show", "_ps")):
            assert t.annotations.read_only_hint is True, t.name
        if any(w in t.name for w in ("delete", "remove", "execute")):
            assert t.annotations.destructive_hint is True, t.name


async def test_read_only_mode_registers_only_read_only_tools(monkeypatch):
    monkeypatch.setenv("OLLAMA_EXECUTE_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_READ_ONLY", "true")
    tools = (await discover_tools_with_handlers()).tools
    assert tools and all(t.annotations.read_only_hint for t in tools)
    assert not {"ollama_pull", "ollama_delete", "ollama_execute"} & {t.name for t in tools}


def test_server_json_matches_registered_tools_and_env():
    sj = json.loads((ROOT / "server.json").read_text())
    ext = sj["_meta"]["io.modelcontextprotocol.registry/publisher-provided"]["cz.vitexsoftware.mcp"]
    assert {t["name"] for t in ext["tools"]} == ALL_TOOLS
    readme = (ROOT / "README.md").read_text()
    for env in sj["packages"][0].get("environmentVariables", []):
        assert env["name"] in readme, env["name"]
