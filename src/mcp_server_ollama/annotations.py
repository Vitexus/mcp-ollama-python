"""Shared MCP tool annotation constants (MCP-SERVER-STANDARDS.md section 1)."""

from mcp.types import ToolAnnotations

# list / show / ps and pure inference (generate, chat, embed): no persistent change.
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True
)
# add / set (same value again is a no-op): ollama_pull.
ASSIGN_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True
)
# delete / full replace: ollama_delete.
MUTATE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True
)
# Arbitrary code execution: irreversible side effects, user confirmation expected.
EXECUTE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=True
)
