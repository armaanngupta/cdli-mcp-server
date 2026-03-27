# CDLI MCP Server Tools Architecture

## Overview

The Model Context Protocol (MCP) server for the CDLI (Cuneiform Digital Library Initiative) database provides a standardized, agent-friendly interface to CDLI's REST API. The tool design is heavily optimized for Large Language Models (LLMs) used in agentic workflows (like literature review, data extraction, and analysis), ensuring reliable performance, reduced context window exhaustion, and simplified tool discovery.

## Tool Design Philosophy

Our tool architecture shifts away from a fragmented "one tool per API endpoint" model towards a **consolidated, intent-driven** model. Instead of providing the LLM with separate tools for `authors`, `publications`, `artifacts`, and `periods`, we provide five orthogonal tools that map directly to the *types of data* an academic agent needs to retrieve.

Key architectural rules:
1. **Aggressive Formatting Restrictions:** We explicitly block the LLM from requesting tabular data (CSV/TSV) or verbose schemas (XML/RDF/Turtle) which rapidly exhaust LLM context limits. The tools strictly enforce JSON, JSON-LD, BibTeX, and simplified Plain Text formats via HTTP `Accept` headers.
2. **Graceful Error Trapping:** 404 (Not Found) and 406 (Not Acceptable) responses are trapped and converted to semantic text responses (e.g., "Resource not found"). This prevents workflow crashes and allows the LLM agent to intelligently course-correct.
3. **Canonical Grounding:** Validations use CDLI canonical data to ensure search parameters are exactly aligned with the database structure before hitting the broader query engine.

## The Tool Reference

### 1. `advanced_search`
- **Description:** The entry point for discovery. Queries the central CDLI search endpoint using precise, fielded parameters (keywords, date ranges, periods, proveniences).
- **LLM Use Case:** "Find me the IDs of all artifacts related to agriculture in the Uruk period."

### 2. `get_cdli_metadata`
- **Description:** Fetches standardized JSON metadata for any specific CDLI catalog entity (artifacts, publications, authors, dynasties, periods, rulers, etc.).
- **LLM Use Case:** "Retrieve the physical characteristics and museum information for artifact P12345."

### 3. `get_cdli_linked_data`
- **Description:** Retrieves the Linked Open Data (JSON-LD) representation of catalog entities.
- **LLM Use Case:** "Extract the semantic relationships and cross-references for this specific archive to build a knowledge graph."

### 4. `get_cdli_bibliography`
- **Description:** Pulls bibliography data for artifacts or publications in strictly academic formats (BibTeX or CSL-JSON).
- **LLM Use Case:** "Generate a proper BibTeX citation for this artifact to append to the research paper."

### 5. `get_cdli_inscription`
- **Description:** Fetches the actual physical text or transliteration of a specific inscription (supports C-ATF, CDLI-CoNLL, and CoNLL-U).
- **LLM Use Case:** "Read the transliteration of this tablet so I can summarize its contents or perform NLP grammar analysis."

### 6. `search_entity`
- **Description:** A unified auto-mapping search tool for non-artifact entities like authors, collections, or materials.
- **LLM Use Case:** "Find the ID for the author Robert Englund so I can look up his profile."
