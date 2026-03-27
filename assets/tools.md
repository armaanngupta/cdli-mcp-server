# CDLI MCP Server Consolidated Tools Plan

Implement the following Model Context Protocol (MCP) server for the cdli.earth REST API. Do not create separate tools for each API endpoint. You must implement exactly the four consolidated tools defined below. Do not make assumptions about data formats or endpoints; follow the schemas and header requirements strictly.

Make the base API URL configurable via an environment variable (e.g., `CDLI_API_BASE_URL`), defaulting to `https://cdli.earth/api` (or the equivalent correct production API path).

## Core Implementation Rules
**Content Negotiation:** You MUST use the `Accept` HTTP header for all requests based on the tools' format parameters. Do not rely on file extensions in the URL path.

**Format Restriction:** Do not implement tabular exports (CSV, TSV, Excel) or XML/RDF/Turtle formats. These waste LLM context window tokens. Restrict outputs to JSON, JSON-LD, BibTeX, CSL-JSON, and plain text inscription formats.

**Error Handling:** If the API returns a 404 or 406 (Not Acceptable), catch the error and return a clean, descriptive string to the LLM (e.g., "Resource not found" or "Format not supported for this resource"). Do not crash the server.

## Tool 1: get_cdli_metadata
**Description:** Fetches standard JSON metadata for any catalog entity (artifacts, publications, authors, dynasties, periods, rulers, etc.).
**API Mapping:** `GET /{resource}/{id}`
**Required Header:** `Accept: application/json`

**Schema:**
```json
{
  "name": "get_cdli_metadata",
  "description": "Fetches standard JSON metadata for CDLI catalog entities. Use this to get details about artifacts, publications, historical periods, rulers, authors, and archives.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "resource": {
        "type": "string",
        "description": "The category to fetch. Supported paths include: artifacts, publications, authors, rulers, dynasties, periods, archives, collections, genres, materials, proveniences."
      },
      "id": {
        "type": "string",
        "description": "The specific ID of the resource. If omitted, returns a paginated list of resources."
      },
      "limit": {
        "type": "number",
        "description": "Number of resources to return if id is omitted (default: 20)."
      },
      "page": {
        "type": "number",
        "description": "Page number for pagination (default: 1)."
      }
    },
    "required": ["resource"]
  }
}
```

## Tool 2: get_cdli_linked_data
**Description:** Fetches Linked Open Data (LOD) representation of catalog data.
**API Mapping:** `GET /{resource}/{id}`
**Required Header:** `Accept: application/ld+json`

**Schema:**
```json
{
  "name": "get_cdli_linked_data",
  "description": "Fetches Linked Open Data (JSON-LD) for CDLI catalog entities.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "resource": {
        "type": "string",
        "description": "The linked data category. Supported paths: archives, artifacts, collections, dates, dynasties, genres, inscriptions, languages, materials, periods, proveniences, publications, regions, rulers."
      },
      "id": {
        "type": "string",
        "description": "The specific ID of the resource."
      }
    },
    "required": ["resource", "id"]
  }
}
```

## Tool 3: get_cdli_bibliography
**Description:** Fetches bibliography exports for artifacts or publications.
**API Mapping:** `GET /{resource}/{id}`
**Header Logic:**
* If format == "BibTeX", use `Accept: application/x-bibtex`
* If format == "CSL-JSON", use `Accept: application/vnd.citationstyles.csl+json`

**Schema:**
```json
{
  "name": "get_cdli_bibliography",
  "description": "Retrieves bibliography export data for artifacts or publications.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "resource": {
        "type": "string",
        "enum": ["artifacts", "publications"],
        "description": "The resource type to get citations for."
      },
      "id": {
        "type": "string",
        "description": "The specific ID of the artifact or publication."
      },
      "format": {
        "type": "string",
        "enum": ["BibTeX", "CSL-JSON"],
        "description": "The requested bibliography format."
      }
    },
    "required": ["resource", "id", "format"]
  }
}
```

## Tool 4: get_cdli_inscription
**Description:** Fetches the transliteration/text of an artifact. Note that the endpoint requires querying the specific artifact's inscription path or the general inscriptions path.
**API Mapping:** `GET /artifacts/{artifact_id}/inscription/{inscription_id}` OR `GET /inscriptions/{id}`. Instruction to agent: For simplicity, route this to `GET /inscriptions/{id}` unless an artifact specifically requires the nested route.
**Header Logic:**
* If format == "C-ATF", use `Accept: text/x-c-atf`
* If format == "CDLI-CoNLL", use `Accept: text/x-cdli-conll`
* If format == "CoNLL-U", use `Accept: text/x-conll-u`

**Schema:**
```json
{
  "name": "get_cdli_inscription",
  "description": "Fetches the physical text or transliteration of a specific inscription.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "The ID of the inscription."
      },
      "format": {
        "type": "string",
        "enum": ["C-ATF", "CDLI-CoNLL", "CoNLL-U"],
        "description": "The format of the inscription text."
      }
    },
    "required": ["id", "format"]
  }
}
```

## Tool 5: search_entity
**Description:** Search across multiple CDLI non-artifact entities (authors, proveniences, languages, collections, materials, regions, periods, genres). This tool maps unified filters to CDLI parameters and normalizes the output.
**API Mapping:** `GET /{entity_type}?{mapped_filters}`
**Required Header:** `Accept: application/json`

**Schema:**
```json
{
  "name": "search_entity",
  "description": "Search across multiple CDLI non-artifact entities (authors, proveniences, languages, collections, materials, regions, periods, genres). This tool maps unified filters to CDLI parameters and normalizes the output.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "entity_type": {
        "type": "string",
        "enum": ["authors", "proveniences", "languages", "collections", "materials", "regions", "periods", "genres"],
        "description": "The type of entity to search for."
      },
      "filters": {
        "type": "object",
        "additionalProperties": { "type": "string" },
        "description": "A key-value map of filters. Use 'name' for general text search. E.g., {'name': 'alexander'}. Other specific keys: 'orcid' (authors), 'region' (proveniences), 'parent' (languages)."
      },
      "limit": {
        "type": "number",
        "description": "Number of results to return (default: 20)."
      },
      "page": {
        "type": "number",
        "description": "Page number for pagination (default: 1)."
      }
    },
    "required": ["entity_type", "filters"]
  }
}
```
