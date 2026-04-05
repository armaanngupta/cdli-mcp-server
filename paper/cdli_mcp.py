"""
Paper-agent data access via MCP tools (stdio transport).

This module keeps the same public function signatures used by the LangGraph
nodes while routing calls through the local MCP server process.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .mcp_client import (
    MCPClientError,
    MCPToolError,
    close_client,
    ensure_tool_success,
    init_client,
    require_client,
)


_CITATION_RE = re.compile(
    r"^\s*(P\d+)\s+[\u2014-]\s+(.+?)\s*$",
    flags=re.MULTILINE,
)
_ARTIFACT_URL_RE = re.compile(r"https?://[^\s]+/artifacts/(\d+)")
_SHOWING_TOTAL_RE = re.compile(r"\(Showing\s+\d+\s+of\s+(\d+)\s+total\s+results\)")


def normalize_artifact_id(artifact_id: str) -> str:
    """Normalize P/Q-prefixed IDs into bare numeric IDs for MCP tools."""
    numeric = str(artifact_id).strip().lstrip("PpQq")
    return numeric


async def init_mcp_client() -> None:
    """Initialize the MCP client used by /paper (idempotent)."""
    await init_client()
    client = require_client()
    tools_result = await client.list_tools()
    tools = tools_result.get("tools")
    if not isinstance(tools, list):
        raise MCPClientError("MCP tools/list returned an invalid payload.")

    tool_names = {
        t.get("name")
        for t in tools
        if isinstance(t, dict) and isinstance(t.get("name"), str)
    }
    required = {"advanced_search", "get_metadata", "get_inscription"}
    missing = sorted(required - tool_names)
    if missing:
        raise MCPClientError(
            f"MCP server is missing required tools for /paper: {', '.join(missing)}"
        )


async def close_mcp_client() -> None:
    """Close the MCP client used by /paper (idempotent)."""
    await close_client()


def _parse_advanced_search_text(text: str) -> dict[str, Any]:
    """
    Parse advanced_search citation text into discovery-compatible shape:
    {"entities": [...], "paging": {"count": ...}}
    """
    if not text:
        return {"entities": [], "paging": {"count": 0}}

    if text.lower().startswith("no artifacts found"):
        return {"entities": [], "paging": {"count": 0}}

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    entities: list[dict[str, Any]] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = _CITATION_RE.match(line)
        if not match:
            i += 1
            continue

        p_id, designation = match.group(1), match.group(2)
        raw_numeric = p_id[1:].lstrip("0") or "0"

        # Prefer numeric ID parsed from following artifact URL when present.
        if i + 1 < len(lines):
            url_match = _ARTIFACT_URL_RE.search(lines[i + 1])
            if url_match:
                raw_numeric = url_match.group(1)
                i += 1

        entities.append(
            {
                "id": raw_numeric,
                "artifact_id": raw_numeric,
                "designation": designation,
            }
        )
        i += 1

    total = len(entities)
    total_match = _SHOWING_TOTAL_RE.search(text)
    if total_match:
        try:
            total = int(total_match.group(1))
        except ValueError:
            total = len(entities)

    return {"entities": entities, "paging": {"count": total}}


def _parse_metadata_text(text: str) -> dict[str, Any]:
    if not text:
        raise MCPToolError("get_metadata returned empty response.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MCPToolError(f"Failed to parse get_metadata JSON: {exc}") from exc

    if isinstance(data, list):
        if len(data) == 0:
            return {}
        first = data[0]
        if isinstance(first, dict):
            return first
        raise MCPToolError("get_metadata returned an unsupported JSON list shape.")

    if isinstance(data, dict):
        return data

    raise MCPToolError("get_metadata returned a non-object JSON response.")


async def advanced_search(params: dict) -> dict:
    """
    Call MCP tool `advanced_search` and normalize output.

    Returns a dict with keys: entities (list), paging (dict).
    """
    params = dict(params)
    params.setdefault("limit", 20)
    params.setdefault("offset", 0)

    client = require_client()
    result = await client.call_tool("advanced_search", params)
    text = ensure_tool_success(result, "advanced_search")
    return _parse_advanced_search_text(text)


async def get_artifact(artifact_id: str) -> dict:
    """
    Fetch artifact metadata via MCP tool `get_metadata`.

    Accepts both prefixed IDs ("P315278") and bare numerics ("315278").
    Returns normalized metadata dict.
    """
    numeric_id = normalize_artifact_id(artifact_id)
    client = require_client()
    result = await client.call_tool(
        "get_metadata",
        {
            "resource": "artifacts",
            "id": numeric_id,
        },
    )
    text = ensure_tool_success(result, "get_metadata")
    return _parse_metadata_text(text)


async def get_translation(artifact_id: str) -> dict:
    """
    Fetch C-ATF inscription text via MCP tool `get_inscription`.

    Returns dict with key "atf" for compatibility with ingestion node.
    """
    numeric_id = normalize_artifact_id(artifact_id)
    client = require_client()
    result = await client.call_tool(
        "get_inscription",
        {
            "id": numeric_id,
            "format": "C-ATF",
        },
    )
    text = ensure_tool_success(result, "get_inscription")
    return {"atf": text}


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

