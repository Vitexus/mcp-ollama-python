# 🦙 Ollama MCP Server (Python)

**Supercharge your AI assistant with local LLM access — run powerful AI models on your own computer, no internet required.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Poetry](https://img.shields.io/badge/Poetry-1.0+-blue)](https://python-poetry.org)
[![MCP](https://img.shields.io/badge/MCP-2.x-green)](https://github.com/modelcontextprotocol/python-sdk)
[![PyPI](https://img.shields.io/pypi/v/mcp-server-ollama)](https://pypi.org/project/mcp-server-ollama/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python [MCP](https://github.com/anthropics/model-context-protocol) server that exposes your local [Ollama](https://ollama.ai) models as tools for AI assistants like **Windsurf**, **VS Code**, **Claude Desktop**, and more.

| | Links |
|---|---|
| **Docs** | [Full documentation](https://pblagoje.github.io/mcp-ollama-python/) |
| **PyPI** | [mcp-server-ollama](https://pypi.org/project/mcp-server-ollama/) |
| **VS Code UI** | Companion extension: [mcp-ollama-extension](https://github.com/pblagoje/mcp-ollama-extension) · [docs](https://pblagoje.github.io/mcp-ollama-extension/) · [Marketplace](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension) |

---

## Ecosystem

These two repositories work together:

```
┌─────────────────────────────────────┐
│  mcp-ollama-extension (VS Code)     │  ← start/stop, models UI, logs
│  https://github.com/pblagoje/       │
│       mcp-ollama-extension          │
└─────────────────┬───────────────────┘
                  │ stdio / MCP
┌─────────────────▼───────────────────┐
│  mcp-server-ollama (this repo)      │  ← MCP tools for Ollama
│  https://github.com/pblagoje/       │
│       mcp-server-ollama             │
└─────────────────┬───────────────────┘
                  │ HTTP :11434
┌─────────────────▼───────────────────┐
│  Ollama                             │
└─────────────────────────────────────┘
```

- **This package** is the MCP server (required). Install with `pip install mcp-server-ollama`.
- **[MCP Ollama Manager](https://github.com/pblagoje/mcp-ollama-extension)** is the optional VS Code UI to manage that server. Prefer it if you use VS Code and want status bar controls, model sidebar, and log viewing without editing JSON by hand.

You can also wire this server into any MCP client (Windsurf, Cursor, Claude Desktop, etc.) without the extension — see [Quick Start](#quick-start) below.

---

## What It Does

Connect your local LLMs to any MCP-compatible AI assistant. No cloud APIs needed.

| Tool | What it does |
|------|-------------|
| `ollama_chat` | Chat with any local model (multi-turn, tool-calling) |
| `ollama_generate` | Generate text completions |
| `ollama_embed` | Create vector embeddings |
| `ollama_list` | List installed models |
| `ollama_show` | Inspect model details |
| `ollama_pull` | Download new models |
| `ollama_delete` | Remove models |
| `ollama_ps` | List running models |

## Quick Start

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.ai) running locally

```bash
pip install mcp-server-ollama
```

**Debian/Ubuntu:**

```bash
sudo apt install mcp-server-ollama            # the server, /usr/bin/mcp-server-ollama
sudo apt install mcprack-mcp-server-ollama    # optional: registers it in the local mcprack catalog
```

> **Renamed:** this project was formerly `mcp-ollama-python`. The Debian package declares
> `Provides/Replaces/Breaks` for the old name and keeps `/usr/bin/mcp-ollama-python` as a
> compatibility symlink. The Python module is now `mcp_server_ollama` (was `mcp_ollama_python`).

### Option A — VS Code with the companion extension (recommended for VS Code)

1. Install [MCP Ollama Manager](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension) from the Marketplace
2. Ensure `mcp-server-ollama` is installed (the extension can offer **Install Now** if missing)
3. Command Palette → **MCP Ollama: Configure Server** → **MCP Ollama: Start Server**

Details: [extension docs](https://pblagoje.github.io/mcp-ollama-extension/) · [repo](https://github.com/pblagoje/mcp-ollama-extension)

### Option B — Any MCP client (Windsurf / VS Code MCP / Cursor / …)

Add to your MCP config (e.g. `mcp_config.json`):

```json
{
  "mcpServers": {
    "ollama": {
      "command": "py",
      "args": ["-m", "mcp_server_ollama"],
      "disabled": false
    }
  }
}
```

Restart your editor — done. Your AI assistant can now use local Ollama models.

### Try It

Type in your AI assistant's chat:

> **MCP Tool: ollama / ollama_chat** — Use model llama3.1 and explain quantum computing

## Key Features

- 🔧 **8 MCP tools** — Full Ollama SDK access
- 🔄 **Hot-swap architecture** — Drop a file in `tools/`, it's auto-discovered
- 🎯 **Type-safe** — Pydantic models throughout
- 🚀 **Lightweight** — Minimal dependencies, fast startup
- 🔌 **Universal** — Works with any MCP client

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](https://pblagoje.github.io/mcp-ollama-python/installation/) | Setup and prerequisites |
| [Available Tools](https://pblagoje.github.io/mcp-ollama-python/tools/) | All tools with examples |
| [Configuration](https://pblagoje.github.io/mcp-ollama-python/configuration/) | Environment variables, model config |
| [Windsurf Integration](https://pblagoje.github.io/mcp-ollama-python/windsurf/) | Complete Windsurf setup guide |
| [VS Code Integration](https://pblagoje.github.io/mcp-ollama-python/vscode/) | VS Code setup + companion extension |
| [Architecture](https://pblagoje.github.io/mcp-ollama-python/architecture/) | How it works, adding tools |
| [Server Control](https://pblagoje.github.io/mcp-ollama-python/SERVER_CONTROL/) | Start/stop/manage the server |
| [Interactive Manager](https://pblagoje.github.io/mcp-ollama-python/mcp_interactive/) | Menu-driven management UI |
| [Development](https://pblagoje.github.io/mcp-ollama-python/development/) | Contributing, code quality |
| [Security](https://pblagoje.github.io/mcp-ollama-python/SECURITY/) | Threat model, host validation, opt-in execute |

## Security (v1.0.8)

- **`ollama_execute` is opt-in** — set `OLLAMA_EXECUTE_ENABLED=1`; shell/bash removed
- **`OLLAMA_HOST` validation** — loopback by default; set `OLLAMA_ALLOW_REMOTE_HOST=1` for LAN/remote Ollama
- **No HTTP redirects** — reduces SSRF risk toward internal endpoints

Details: [docs/SECURITY.md](docs/SECURITY.md)

## Changelog

### 1.1.0

- Migrated to **MCP Python SDK 2.x** (`mcp>=2.0.0,<3.0.0`)
- Low-level server handlers now use SDK 2 `on_*` constructor callbacks and snake_case types

### 1.0.8

- Security hardening: host validation, execute tool gating, env allowlist, input limits
- Fixed `__version__` mismatch with package version
- Added `tests/test_security.py` and `docs/SECURITY.md`

## Related Projects

| Project | Role | Links |
|---------|------|-------|
| **[mcp-ollama-extension](https://github.com/pblagoje/mcp-ollama-extension)** | VS Code UI for this server | [GitHub](https://github.com/pblagoje/mcp-ollama-extension) · [Docs](https://pblagoje.github.io/mcp-ollama-extension/) · [Marketplace](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension) |
| [Ollama](https://ollama.ai/) | Local LLM runtime | [ollama.ai](https://ollama.ai/) |

## License

[MIT](LICENSE)

---

<div align="center">

Made with ❤️ using Python, Poetry, and Ollama

</div>
