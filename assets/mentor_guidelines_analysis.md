# CDLI AI Research Interface — Mentor Guidelines Analysis & Execution Plan

## Summary of Mentor's Vision

The mentor has a significantly larger vision than a basic MCP server. The project is called the **CDLI AI Research Interface** and consists of three interconnected components:

1. **AI Search Button** — embedded on `cdli.earth` under "Corpus Search", labeled "AI Search"
2. **AI Research Workspace** — a separate standalone web app with LLM chat, BYOM (Bring Your Own Model) key support
3. **CDLI MCP Server** — the backend tool layer that both the workspace and external clients call

---

## What We Were Doing Correctly

- ✅ Building a TypeScript MCP server using the official SDK
- ✅ Modular tool structure — each tool in its own folder
- ✅ Using `cdli.earth` as the base API URL
- ✅ Exposing artifact retrieval, search, authors, publications, proveniences
- ✅ Correct understanding of stdio transport for Claude Desktop
- ✅ Clean ATF inscription embedded in `get_artifact` response

---

## What We Were Missing / Doing Differently

| What we assumed | What the mentor actually wants |
|---|---|
| MCP server is the final product | MCP server is only one of three components |
| CLI/Claude Desktop integration as demo | A full standalone browser-based AI Research Workspace |
| Simple search by keyword | Full Advanced Search field support (language, genre, period, provenience, artifact type, translation text, etc.) |
| No CQP integration | CQP-to-RDF must be exposed as an MCP tool |
| No frontend | A separate web app UI with multi-LLM provider support |
| Artifact data returned as JSON | All AI outputs must include standardized artifact citations with URLs |
| Standalone server | MCP server integrated with CDLI website's "AI Search" button |

---

## Full MCP Tool Set Required

Based on the mentor's spec, these are the tools the MCP server must expose:

| Tool Name | Purpose |
|---|---|
| `search_artifacts` | Natural language → CDLI search parameters |
| `advanced_search` | Structured search across all fields from `/search/advanced` |
| `get_artifact` | Full artifact metadata retrieval |
| `get_translation` | Extract `atf_translation_text` from an artifact |
| `cqp_query` | Run a CQP linguistic query via `cdli.earth/cqp4rdf/` |
| `get_authors` | List CDLI authors |
| `get_publications` | List publications |
| `get_provenience` | List proveniences |
| `ping` | Liveness check |

---

## System Architecture (As Mentor Envisions It)

```
cdli.earth (Website)
    │
    └── "AI Search" button (under Corpus Search)
            │
            ▼
    AI Research Workspace (Standalone Web App)
            │
            ├── Multi-LLM Provider Selection (OpenAI, Anthropic, Google, Mistral)
            ├── BYOM — user adds own API key
            ├── Chat interface
            └── MCP Client
                    │
                    ▼
        CDLI MCP Server (HTTP/SSE transport for web, stdio for desktop)
            ├── search_artifacts
            ├── advanced_search
            ├── get_artifact
            ├── get_translation
            ├── cqp_query
            └── (+ existing tools)
                    │
                    ▼
        CDLI APIs (cdli.earth REST + CQP-to-RDF system)
```

---

## Execution Plan

### Phase 1 — Expand the MCP Server Tools (Priority)
**Goal:** Cover all fields from the Advanced Search page and add CQP tool.

1. **`advanced_search` tool**
   - Study all query params at `https://cdli.earth/search/advanced`
   - Accept fields: `language`, `genre`, `period`, `provenience`, `artifact_type`, `translation_text`, `museum_no`, `publication`
   - Return artifacts with citation links (format: `P254876 — Title\nhttps://cdli.earth/artifacts/254876`)

2. **`get_translation` tool**
   - Takes an artifact ID
   - Returns only the `atf_translation_text` field from the artifact
   - Separate from `get_artifact` so the LLM can request just the text without the full JSON

3. **`cqp_query` tool**
   - Study the CQP-to-RDF project: `https://cdli.earth/cqp4rdf/` and its API
   - Accept a CQP expression like `[lemma="rain"]`
   - Return matching artifact references with citation links

4. **Artifact citation standard**
   - All tools must return results in the format: `P254876 — Rain invocation ritual\nhttps://cdli.earth/artifacts/254876`

### Phase 2 — HTTP/SSE Transport
**Goal:** Switch from stdio-only to supporting HTTP/SSE for web app use.

- The MCP SDK supports `SSEServerTransport`
- Add a second server entrypoint (`src/http-server.ts`) using Express + SSE
- Keep stdio as the default (for Claude Desktop compat), HTTP as opt-in

### Phase 3 — AI Research Workspace (Frontend)
**Goal:** Build the standalone web app that serves as the primary user interface.

- A React or plain HTML/JS single-page app
- Multi-provider LLM selection UI (OpenAI, Anthropic, Google, Mistral)
- User enters their own API key (stored in browser `localStorage`, never sent to CDLI server)
- Chat interface that connects to the CDLI MCP server via HTTP/SSE
- Each AI message should render artifact citations as clickable links

### Phase 4 — Research Paper Agent
**Goal:** An agent workflow that generates structured research outputs.

- User provides a topic (genre/period/language/keyword)
- Agent calls `advanced_search` + `get_translation` repeatedly
- Clusters results by theme
- Produces an academic-style draft with sections: Abstract, Introduction, Corpus Overview, Textual Evidence, Discussion, References
- All references are CDLI artifact citation links

---

## Required Knowledge to Execute

| Area | What to Learn |
|---|---|
| **MCP Protocol** | HTTP/SSE transport in addition to stdio — [docs](https://modelcontextprotocol.io/docs/develop/build-server) |
| **CDLI Advanced Search API** | Study all query parameters at `https://cdli.earth/search/advanced` |
| **CQP-to-RDF** | Study the GSoC project by Saga Sehgal and its API interface at `https://cdli.earth/cqp4rdf/` |
| **LLM Provider SDKs** | Basic usage of OpenAI, Anthropic, and Google SDK for chat completions |
| **SSE (Server-Sent Events)** | How browsers receive streaming responses from a server |
| **Frontend (React or vanilla JS)** | Building the AI Research Workspace UI |

---

## Notes

- The CQP-to-RDF integration is likely the most complex and research-heavy part. Start by reading the existing project docs carefully.
- The BYOM (Bring Your Own Key) design means CDLI never needs to pay for LLM API costs — the user always provides the key.
- The AI Search button on the CDLI website itself is likely out of GSoC scope unless the mentor includes CakePHP frontend work — clarify this boundary.
