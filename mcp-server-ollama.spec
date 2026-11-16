# -*- mode: python ; coding: utf-8 -*-
# from terminal/cli, run: poetry shell & pyinstaller mcp-server-ollama.spec --clean --distpath bin
# or from poetry, run: poetry run pyinstaller mcp-server-ollama.spec --clean --distpath bin

import os
import platform
import re
import struct
from pathlib import Path

# ---------------------------------------------------------------------------
# Read version from pyproject.toml
# ---------------------------------------------------------------------------
_pyproject = Path(SPECPATH) / "pyproject.toml"
try:
    import tomllib
    _version_str = tomllib.loads(_pyproject.read_text(encoding="utf-8"))["tool"]["poetry"]["version"]
except Exception:
    _m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', _pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    _version_str = _m.group(1) if _m else "0.0.0"

_ver_parts = [int(x) for x in _version_str.split(".")]
while len(_ver_parts) < 4:
    _ver_parts.append(0)
_ver_tuple = tuple(_ver_parts[:4])

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

_version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=_ver_tuple,
        prodvers=_ver_tuple,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "Pedja Blagojevic"),
                        StringStruct("FileDescription", "MCP Ollama Python Server"),
                        StringStruct("FileVersion", _version_str),
                        StringStruct("InternalName", "mcp-server-ollama"),
                        StringStruct("OriginalFilename", "mcp-server-ollama.exe"),
                        StringStruct("ProductName", "MCP Ollama Python"),
                        StringStruct("ProductVersion", _version_str),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

# ---------------------------------------------------------------------------
# Detect OS and architecture for the EXE filename
# ---------------------------------------------------------------------------
_arch = "x64" if struct.calcsize("P") * 8 == 64 else "x86"

_os_tag = os.environ.get("MCP_OS_TAG", "")
if not _os_tag:
    if platform.system() == "Windows":
        _win_ver = platform.version()  # e.g. "10.0.22631"
        _build = int(_win_ver.split(".")[-1]) if _win_ver else 0
        if _build >= 22000:
            _os_tag = "win11"
        else:
            _os_tag = "win10"
    elif platform.system() == "Darwin":
        _os_tag = f"macos{platform.mac_ver()[0]}"
    else:
        _os_tag = "linux"

_exe_name = f"mcp-server-ollama-{_version_str}-{_os_tag}-{_arch}"

block_cipher = None

a = Analysis(
    ['src/mcp_server_ollama/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Standard library
        'asyncio',
        'signal',
        'sys',
        'typing',
        # Timezone data
        'tzdata',
        # MCP dependencies
        'mcp',
        'mcp.server',
        'mcp.server.stdio',
        'mcp.types',
        'mcp.shared',
        'mcp.shared.memory',
        # HTTP client
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        # Pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        # Rich console
        'rich',
        'rich.console',
        'rich.logging',
        # System utilities
        'psutil',
        # JSON handling
        'json',
        'jsonschema',
        # Internal modules
        'mcp_server_ollama',
        'mcp_server_ollama.server',
        'mcp_server_ollama.ollama_client',
        'mcp_server_ollama.models',
        'mcp_server_ollama.response_formatter',
        'mcp_server_ollama.autoloader',
        'mcp_server_ollama.tools',
        'mcp_server_ollama.tools.chat',
        'mcp_server_ollama.tools.delete',
        'mcp_server_ollama.tools.embed',
        'mcp_server_ollama.tools.generate',
        'mcp_server_ollama.tools.list',
        'mcp_server_ollama.tools.ps',
        'mcp_server_ollama.tools.pull',
        'mcp_server_ollama.tools.show',
        # Async support
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'sniffio',
        # SSL/HTTP support
        'certifi',
        'httpcore',
        'h11',
        'idna',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=_exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=_version_info,
)
