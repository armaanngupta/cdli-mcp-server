"""
Thin async HTTP client wrapping the CDLI REST API.

All functions mirror the MCP server tools so the agent calls the same
live endpoints without going through the MCP transport layer.
Timeouts are capped at 8 seconds — matching the MCP server config.
"""

import httpx

_BASE = "https://cdli.earth"
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "cdli-paper-agent/1.0.0",
}
_TIMEOUT = 8.0


async def advanced_search(params: dict) -> dict:
    """
    Call the CDLI advanced search endpoint.
    `params` mirrors the advanced_search tool's inputSchema fields
    (period, language, genre, provenience, limit, offset, …).
    Returns a dict with keys: entities (list), paging (dict).
    """
    params.setdefault("limit", 20)
    params.setdefault("offset", 0)

    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        r = await client.get(f"{_BASE}/search.json", params=params)
        r.raise_for_status()
        data = r.json()

    # Normalise response shape: the API returns either a dict with
    # an "entities" list, or a bare list.
    if isinstance(data, list):
        return {"entities": data, "paging": {"count": len(data)}}
    return data


async def get_artifact(artifact_id: str) -> dict:
    """
    Fetch full metadata for a single artifact.
    Accepts both prefixed IDs ("P315278") and bare numerics ("315278").
    Returns the raw artifact JSON dict.
    """
    numeric_id = artifact_id.lstrip("PpQq")
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        r = await client.get(f"{_BASE}/artifacts/{numeric_id}.json")
        r.raise_for_status()
        return r.json()


async def get_translation(artifact_id: str) -> dict:
    """
    Fetch the ATF transliteration for a single artifact.
    Returns whatever the /inscription endpoint provides.
    """
    numeric_id = artifact_id.lstrip("PpQq")
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        r = await client.get(f"{_BASE}/artifacts/{numeric_id}/inscription")
        r.raise_for_status()
        return r.json()
