"""
Compatibility shim.

Historically this module talked to CDLI's REST API directly. The /paper workflow
now routes CDLI access through the local MCP server over stdio.

New code should prefer importing from `paper.cdli_mcp`.
"""

from .cdli_mcp import (  # noqa: F401
    MCPClientError,
    MCPToolError,
    _parse_advanced_search_text,
    _parse_metadata_text,
    advanced_search,
    close_mcp_client,
    get_artifact,
    get_translation,
    init_mcp_client,
    normalize_artifact_id,
)

__all__ = [
    "MCPClientError",
    "MCPToolError",
    "advanced_search",
    "get_artifact",
    "get_translation",
    "init_mcp_client",
    "close_mcp_client",
    "normalize_artifact_id",
    "_parse_advanced_search_text",
    "_parse_metadata_text",
]
