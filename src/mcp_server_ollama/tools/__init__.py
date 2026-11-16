"""
Ollama MCP Tools Package

This package contains tools for interacting with Ollama models via MCP protocol.
Tools are automatically discovered by the autoloader at runtime.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = ["__version__"]
try:
    __version__ = version("mcp-server-ollama")
except PackageNotFoundError:  # pragma: no cover - not installed (e.g. source tree)
    try:
        __version__ = version("mcp-ollama-python")
    except PackageNotFoundError:
        __version__ = "0+unknown"
