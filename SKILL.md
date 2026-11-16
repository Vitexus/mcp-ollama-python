---
name: mcp-server-ollama
description: Use the local Ollama MCP server to list/pull/delete models, chat, generate text and compute embeddings with models running on the user's own machine.
---

# Ollama MCP server

Tools: `ollama_list`, `ollama_show`, `ollama_pull`, `ollama_delete`, `ollama_ps`,
`ollama_chat`, `ollama_generate`, `ollama_embed`, `ollama_execute` (opt-in, needs `OLLAMA_EXECUTE_ENABLED=true`).

- Prefer `ollama_list` first to see which models are installed before chatting.
- `ollama_pull` / `ollama_delete` change local state — confirm with the user.
- `OLLAMA_HOST` must be local unless `OLLAMA_ALLOW_REMOTE_HOST=true`.
