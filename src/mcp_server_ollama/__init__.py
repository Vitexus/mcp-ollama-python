"""
Package initialization for mcp_server_ollama.

This module provides the main entry point and package-level exports.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from .main import run

__all__ = ["run", "__version__"]
try:
    __version__ = version("mcp-server-ollama")
except PackageNotFoundError:  # pragma: no cover - not installed (e.g. source tree)
    try:
        __version__ = version("mcp-ollama-python")
    except PackageNotFoundError:
        __version__ = "0+unknown"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
