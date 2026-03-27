# Implementation Details – `advanced_search` MCP Tool

## Goal
Provide a high‑performance MCP tool that mirrors CDLI’s **Advanced Search** endpoint, exposing all searchable fields as optional parameters and returning results in the standard citation format.

## Design Overview
| Component | Responsibility |
|---|---|
| **Tool module** ([src/tools/advanced-search/index.ts](cci:7://file:///home/armaanngupta/zeesoc/cdli-mcp-server/src/tools/advanced-search/index.ts:0:0-0:0)) | Validate input, map parameters to URL query string, call `https://cdli.earth/search.json`, format results. |
| **Parameter mapping** (`FIELD_PARAMS` constant) | 1‑to‑1 mapping from tool argument names to CDLI query parameters. |
| **Pagination** | [limit](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:790:4-795:5) (default 20, max 100) and [offset](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:797:4-802:5) (default 0) are added to every request. |
| **Result formatting** | Convert each returned entity to `P###### — <designation>` with a link to the artifact page. |
| **Error handling** | Network errors and non‑200 HTTP responses are reported as tool errors. |

## Input Schema
All fields are optional strings (or numbers for pagination), matching the advanced‑search UI:

- **Identifiers**: `designation`, `museum_no`, `accession_no`, `excavation_no`, `cdli_id`
- **Bibliographic**: `publication_designation`, `publication_authors`, `publication_editors`, `publication_year`, `publication_title`, `publication_type`, `publication_publisher`, `publication_series`
- **Artifact properties**: `artifact_type`, `material`, `period`, `provenience`, `collection`, `archive`, `genre`, `language`, `dates_referenced`
- **Textual**: `atf_transliteration`, `atf_translation_text`, `atf_comments`
- **Composite/Seal**: `composite_no`, `seal_no`, `all_composite_no`, `all_seal_no`
- **Contributor**: `update_authors`
- **Pagination**: [limit](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:790:4-795:5) (number), [offset](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:797:4-802:5) (number)

Values may contain CDLI‑specific syntax (`%AND%`, `%OR%`, wildcards, regex) – the tool forwards them unchanged.

## Execution Flow
1. **Collect args** – read all supplied arguments.  
2. **Build query string** – start with [limit](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:790:4-795:5)/[offset](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:797:4-802:5), then iterate over `FIELD_PARAMS` and add any non‑empty values.  
3. **Validate presence** – if no field is supplied, return a user‑error prompting for at least one filter.  
4. **HTTP request** – `fetch` the constructed URL with `Accept: application/json` and a custom `User-Agent`.  
5. **Handle response** – on success, parse JSON, extract the `entities` array, and build citation strings.  
6. **Return** – a single `text` content block containing the formatted citations (or a “no results” message). Errors are flagged with `isError: true`.

## Result Formatting
Each entity is turned into the standard citation:


If pagination returns a subset, a note is added:  
[(Showing 20 of 342 total results)](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:222:4-259:5)

## Verification Plan
- **Unit test**: invoke the handler with a minimal set of parameters (e.g. `{ period: "Ur III" }`) and assert that the generated URL contains `period=Ur+III` and pagination defaults.  
- **Integration test**: run the MCP server, call the tool via the `CallTool` RPC, and verify that the response matches the citation format for a known artifact.  
- **Error cases**: simulate a non‑200 HTTP response and a network exception; ensure `isError` is true and the message is informative.  
- **Performance**: confirm the request completes < 2 s for typical queries (run locally with `time`).  

## Future Extensions
- Add **field‑level validation** (e.g., numeric range checks for `publication_year`).  
- Support **sorting** via an optional [order](cci:1://file:///home/armaanngupta/zeesoc/framework/app/cake/src/Datasource/ElasticSearchQuery.php:119:4-122:5) param.  
- Expose **total count** in the response metadata for UI pagination.

### Grounding for misspelled terms

User input may contain typos (e.g., "nipuur" instead of "Nippur"). The `advanced_search` handler now calls the `ground_term` tool for fields such as `provenience`, `period`, `collection`, `genre`, and `language`. The grounding tool performs a fuzzy match against a canonical list of CDLI terms and returns the closest spelling. The corrected value is substituted into the query before the API call, preventing empty‑result failures. If no confident match is found, the tool returns the original value and the LLM can ask the user for clarification.

#### Edge Cases & Robustness Considerations (Future Work)
While the current grounding implementation handles basic typos, a production-ready system should also account for:
- **Ambiguous or Low-Confidence Terms**: Currently addressed by only substituting terms with Levenshtein distance $\le 2$.
- **Silent Semantic Drift**: To ensure users' scholarly intent isn't unintentionally altered, a correction log should be surfaced in responses so the user knows what substitution occurred.
- **Multi-Value Queries**: Fields containing `%AND%` / `%OR%` operators should ideally be tokenized, and grounding applied to each term independently without breaking logic.
- **Zero-Result Queries After Grounding**: A fallback strategy to retry the query using a relaxed match if the grounded term yields 0 results.
- **Repeated Grounding Overhead**: Caching `raw → grounded` dictionary mappings for the lifetime of the server process to improve latency instead of re-evaluating distances frequently.

*Generated on 2026‑03‑25.*  
