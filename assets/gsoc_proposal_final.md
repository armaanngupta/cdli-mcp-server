## 1. Project Overview
This project proposes an AI Research Interface for CDLI using the open Model Context Protocol (MCP) standard. Currently, finding specific information among CDLI's 400,000+ ancient tablets is difficult because it requires knowing exact search terms and complex form structures. The proposed solution addresses this by building an MCP Server that translates plain-English questions into proper CDLI searches, alongside a chat widget that lives directly on the CDLI website. This provides researchers with an interactive, on-site assistant without costing CDLI any money for AI API usage, as users can securely plug in their own API keys. It also allows external AI tools like Claude, Cursor, and Windsurf to connect directly to the CDLI database.

---
*(Note: For architectural diagrams, UI mockups, and a working prototype, please see the supplementary repository: [github.com/armaanngupta/cdli-mcp-server-assets](https://github.com/armaanngupta/cdli-mcp-server-assets))*

## 2. Project Goals & Deliverables

### Goals
- **Make Searching Easy**: Allow users to ask natural language questions instead of learning complex search forms and syntax.
- **Connect with Outside Tools**: Let researchers query CDLI directly from the desktop AI tools they already use (like Claude or Cursor).
- **Keep Costs at Zero**: Use a "Bring Your Own Key" setup so CDLI never has to pay for the AI tokens used in searches.
- **Provide Accurate Citations**: Force the AI to always point back to real CDLI artifact IDs (e.g., *P254876*) instead of guessing or making things up.

### Expected Deliverables
1. **MCP Server**: A fully functional backend hosted on CDLI's infrastructure that turns database queries into AI-ready tools.
2. **AI Research Workspace**: A chat widget embedded directly on the CDLI website that harnesses the MCP server to answer researcher queries.
3. **Documentation**: Thorough development guides and setup instructions so future maintainers can easily understand and expand the project.
4. **Third-Party Integrations**: The configuration required so external researchers can connect their desktop AI tools (like Claude or Cursor) directly to the CDLI server.

---

## 3. Project Architecture

At a high level, the project has two major components — the **MCP Server** and the **AI Research Widget** — connected by a standard HTTP/SSE transport layer.

> 📎 **Visual**: Insert the **Simple Flow Diagram** (`simple_flow_diagram.html`) here — a 5-step bird's-eye view of how a user question travels through the system and comes back as a cited answer.

The MCP Server sits between the AI client (whether the CDLI website widget or a desktop tool like Claude) and the CDLI database APIs. It defines a fixed set of structured "tools." When a researcher asks a question, the AI picks the right tool, the server calls the CDLI API, and the result flows back as clean, formatted text.

The two key interaction patterns are:

- **Web Widget path**: The floating chat widget on `cdli.earth` connects to the hosted MCP server at `mcp.cdli.earth` over SSE. The widget sends the user's message to the LLM, which in turn calls MCP tools and streams the response back to the browser.
- **Desktop client path**: A researcher using Claude Desktop or Cursor adds the CDLI server as an MCP source in their local config. Their local AI client connects via stdio or SSE and gets the same tools.

> 📎 **Visual**: Insert the **System Architecture Diagram** (`architecture_diagram.html`) here — a structural view of the two client paths connecting to the shared MCP server and the CDLI APIs.


The MCP server exposes the following tools to AI clients:

| Tool | Purpose |
|---|---|
| `advanced_search` | Filtered search by period, language, provenience, or genre |
| `get_artifact` | Full metadata for a specific artifact by ID |
| `get_translation` | English translation and ATF transliteration for a tablet |
| `cqp_query` | Linguistic pattern search using CQP expressions |
| `get_authors` | List of authors associated with a given text |
| `get_publications` | Publication references for a given artifact |
| `get_provenience` | Site and geographical data for a tablet |

Each tool is self-contained and independently testable. The AI client discovers all available tools automatically when it connects, so adding new tools in the future requires no changes to the client side.

The diagram below shows the **flow of a complex query** through the system — from user input to the final response. The LLM iterates through tools (searching, then fetching translations) until it has everything it needs to give a complete answer.

> 📎 **Visual**: Insert the **Complex Prompt Flow Diagram** (`complex_prompt_flow.html`) here — shows the agent loop logic: LLM selects a tool, evaluates the result, and decides whether to call another tool or compose the final response.


---

## 5. Method & Approach

The project is split across four sequential phases. Each one builds on top of the last, ensuring that progress is testable and demonstrable at every step.

---

### 5.1. Phase 1: Core MCP Server & Modular Tool Design

The first phase is about building the server that bridges natural language questions and the CDLI database. Each CDLI capability (searching, fetching artifact details, running a linguistic query) will be defined as a separate, self-contained MCP "tool."

The key tools planned are:

| Tool | What it does |
|---|---|
| `advanced_search` | Filtered search by period, language, provenience |
| `get_artifact` | Fetches full metadata and details for one ID |
| `get_translation` | Fetches the English translation and ATF text |
| `cqp_query` | Runs a linguistic CQP pattern match on the corpus |
| `get_authors` | Lists known authors linked to a text |
| `get_publications` | Retrieves associated publication references |
| `get_provenience` | Returns site provenance for a given tablet |

Each tool is defined with a `name`, a `description` (which the LLM reads to decide when to use the tool), and an `inputSchema` (which enforces what arguments are valid). The following are the actual tool definitions from the working prototype:

```typescript
// ── Tools implemented in the prototype ──

// ─────────────────────────────────────────

export const name = "get_artifact";
export const description = "Get full metadata for a specific CDLI artifact by ID, including its publications, materials, period, provenience, collections, and the full ATF inscription/transliteration text.";
export const inputSchema = {
  type: "object",
  properties: {
    id: { type: "string", description: "The artifact ID (e.g. P315278 or 315278)" }
  },
  required: ["id"]
};

// ─────────────────────────────────────────

export const name = "get_translation";
export const description = "Get the inscription (transliteration text) for a specific CDLI artifact by its ID.";
export const inputSchema = {
  type: "object",
  properties: {
    id: { type: "string", description: "CDLI artifact ID — accepts both P315278 and 315278 formats" }
  },
  required: ["id"]
};

// ─────────────────────────────────────────

export const name = "get_authors";
export const description = "Get a list of CDLI authors";
export const inputSchema = { type: "object", properties: {} };

// ─────────────────────────────────────────

export const name = "get_publications";
export const description = "Get a list of publications from the CDLI database. Optionally limit the number of results.";
export const inputSchema = {
  type: "object",
  properties: {
    limit: { type: "number", description: "Number of publications to return (default: 20)" }
  }
};

// ─────────────────────────────────────────

export const name = "get_provenience";
export const description = "Get a list of proveniences (archaeological find sites) from the CDLI database. Optionally limit results.";
export const inputSchema = {
  type: "object",
  properties: {
    limit: { type: "number", description: "Number of proveniences to return (default: 20)" }
  }
};

// ── Planned: CQP-to-RDF linguistic tool ──

export const name = "cqp_query";
export const description = "Run a CQP (Corpus Query Processor) linguistic pattern search against the CDLI corpus via the CQP-to-RDF API.";
export const inputSchema = {
  type: "object",
  properties: {
    expression: { type: "string", description: "A valid CQP expression, e.g. [lemma='lugal' & pos='N']" }
  },
  required: ["expression"]
};
```

> 📎 **Visual**: Insert the **System Architecture Diagram** (`architecture_diagram.html`) here — shows the MCP server sitting between the AI clients and the CDLI APIs.

---

### 5.2. Phase 2: Implementing the Hybrid Transport Layer

Once the tools are built, the server needs to support two different ways to communicate, because it will be used from two very different environments:

- **stdio transport**: Used by desktop AI clients (like Claude Desktop or Cursor) that run the server as a local background process on the researcher's own machine.
- **HTTP/SSE transport**: Used by the browser-based chat widget on the CDLI website, which needs a persistent connection to a publicly hosted server over the internet.

The server will detect the environment at startup and switch between transports automatically. The HTTP/SSE variant will be packaged into a Docker container and hosted at a stable endpoint (e.g., `mcp.cdli.earth`), allowing external tools to connect without any local setup.

Connecting from Claude Desktop requires only a single config entry:
```json
"cdli": {
  "command": "npx",
  "args": ["-y", "@cdli/mcp-server"]
}
```

> 📎 **Visual**: Insert the **Interoperability "Hub" Diagram** (`interoperability_diagram.html`) here — shows all the different clients (Claude, Cursor, the widget) pointing at the one hosted server.

---

### 5.3. Phase 3: Developing the Context-Aware AI Widget

Instead of a full, separate web app, the AI interface will be a small floating chat button on the CDLI website — like Intercom or Zendesk — that opens a chat drawer on the side of the screen. It works on every page of the site with no separate navigation required.

Integrating this into the existing CakePHP codebase requires only one line change in the global layout template:

```php
<!-- In /templates/layout/default.php -->
<div id="cdli-ai-widget-root"></div>
<script type="module" src="https://cdli.earth/assets/ai-widget/bundle.js"></script>
```

The widget connects to the hosted MCP server via SSE. Researchers enter their own API key (OpenAI, Anthropic, Gemini) once in the settings panel. The key stays entirely in the browser — it never touches CDLI's servers. The widget supports:
- Markdown rendering for clean, readable responses
- Inline artifact citation cards (with artifact ID, period, and a direct link)
- Slash commands (`/search`, `/artifact`, `/cqp`, `/paper`) for quick, structured workflows

> 📎 **Visuals**: Insert the **Widget Open Drawer** (`ai_widget_mockup.html`), **Widget Folded Bubble** (`ai_widget_mockup_folded.html`), and **Slash Command Picker** (`ai_widget_mockup_commands.html`) mockups side by side here.

#### Making the widget tool-aware

Tool awareness is handled automatically by the MCP protocol handshake. When the widget opens an SSE connection to `mcp.cdli.earth`, the server responds with the full **tool manifest** — the name, description, and JSON Schema of every available tool. The widget prepends this manifest to the LLM's system prompt on every turn. The LLM therefore knows exactly which tools exist and how to call them without any custom routing logic in the widget code.

#### System prompt (base, injected on every turn)

Every conversation turn sent from the widget includes the following system context, regardless of which slash command is active:

```
SYSTEM:

You are an AI research assistant for the Cuneiform Digital Library Initiative (CDLI).
You have access to the following tools provided by the CDLI MCP server:
  - advanced_search(filters)        — filtered search by period, language, provenience, genre
  - get_artifact(id)                — full metadata for one artifact by CDLI ID
  - get_translation(id)             — English translation + ATF transliteration for one artifact
  - cqp_query(expression)           — linguistic CQP pattern search
  - get_authors / get_publications / get_provenience — reference lookups

Rules that apply to every response:
1. When referencing CDLI artifacts, cite their CDLI IDs.
2. Do NOT invent artifact IDs, translations, or metadata. If a tool returns no result, say so.
3. Do NOT paste raw ATF transliteration into output; always paraphrase.
4. You may call at most 5 tools per turn. If more are needed, ask the user to continue.
```

Slash commands like `/paper` extend this base prompt with additional phase-specific instructions injected at the top of the turn.

#### Expected context length

The widget is designed to stay well within the context windows of free-tier and low-cost API tiers (8k–16k tokens). The per-turn token budget is:

| Budget item | Approx. tokens |
|---|---|
| Base system prompt + tool manifest | ~1,200 |
| Conversation history (last 3 turns) | ~600 |
| Slash-command phase instructions (e.g. `/paper`) | ~400 |
| Single tool response (`get_artifact`, key fields only) | ~400 |
| **Typical turn total (standard query)** | **~2,200** |
| **Peak turn total (`/paper` ingestion phase)** | **~3,800** |

For the `/paper` command specifically, cumulative context across both ingestion turns (10 artifact summaries + history) peaks at roughly **6,000–7,000 tokens** before synthesis — well within all supported models' limits.

---

### 5.3.1. Research Paper Generation Agent (`/paper`)

The `/paper` command is the most sophisticated slash command and is a first-class deliverable specified by the project mentor (see Section 7 of the Product Specification). It triggers a **multi-phase agentic workflow** that constrains the LLM to a safe, context-aware pipeline — preventing the context-window explosion that would occur if the agent tried to ingest dozens of full artifact transliterations at once.

No dedicated agent orchestration framework (e.g. LangChain, LangGraph, AutoGen) is used. The workflow is implemented as a **prompt-based agentic pipeline**: a structured system prompt encodes all four phases as explicit, sequenced instructions, and the LLM acts as its own orchestrator by following them. Hard behavioural limits are enforced at the server level (the 5-tool-call-per-turn cap), not in application code — meaning the LLM cannot deviate from the phase structure even if it wanted to. This keeps the stack as plain TypeScript + the MCP SDK, with no additional dependencies, making the project far easier for future CDLI maintainers to understand and extend. A graph-based framework like LangGraph would add more robustness against prompt deviation but would introduce a significant architectural dependency outside the project's scope.

When a user types `/paper <topic>`, the widget intercepts the input and injects a structured system prompt that instructs the LLM to follow a four-phase sequence:

**Phase 1 — Discovery:** The LLM calls `advanced_search` with the research topic, collecting only artifact IDs, periods, genres, and proveniences — not full text. After this phase, the agent pauses and reports how many artifacts were found, asking the user to confirm before proceeding.

**Phase 2 — Scoping (no tool calls):** The LLM ranks the discovered artifacts by relevance using their metadata alone — prioritising genre match, translation availability, and period alignment with the topic. It selects a hard cap of **10 artifacts** and presents the shortlist with a one-line justification for each. This step costs zero tokens in API calls.

**Phase 3 — Sequential Ingestion:** The LLM calls `get_artifact` for **one artifact at a time**, writing a 3-sentence summary immediately after each retrieval before loading the next. For the 3 most relevant artifacts, it additionally calls `get_translation` and extracts key passages. The full artifact text is never held in context alongside other artifacts — it is summarised and discarded before the next one is loaded. Because the existing 5-tool-call-per-turn limit applies, ingestion spans two turns (5 artifacts each), with a pause between them requiring the user to type "continue".

**Phase 4 — Synthesis:** Working exclusively from the accumulated summaries (no further tool calls), the LLM generates the final research output in the structure specified by the mentor:

> **Abstract** — A 150-word overview of the research topic and corpus coverage.
> **Introduction** — Context on the historical/linguistic significance of the topic.
> **Corpus Overview** — Summary of the artifact set: count, periods, proveniences, languages represented.
> **Textual Evidence** — Thematic analysis citing specific tablets by CDLI ID.
> **Discussion** — Comparative observations and scholarly implications.
> **References** — Every cited artifact as a CDLI citation: `P254876 — Rain invocation ritual · https://cdli.earth/artifacts/254876`

Every factual claim in the output is anchored to a real CDLI artifact ID. The agent is explicitly prohibited from generating claims without a corresponding citation, which directly prevents hallucination of artifact content.

> 📎 **Visual**: Insert the **`/paper` Agentic Workflow Diagram** (`paper_workflow_diagram.png`) here — shows the four phases, the per-turn tool-call budget, and the guardrails (max 10 artifacts, no raw ATF in output, graceful timeout handling).

**Guardrails built into the workflow:**
- Maximum 10 artifacts per `/paper` invocation, regardless of how many the search discovers.
- If any tool call fails or times out, that artifact is skipped and noted as unavailable in the References section — the pipeline does not abort.
- Raw ATF transliteration text is never pasted directly into the output; the LLM always paraphrases from its own summary.
- The workflow operates across multiple short turns rather than one massive request, keeping each individual API call well within token-per-minute limits.

---

### 5.4. Anticipated Technical Challenges & Mitigations

| Challenge | Mitigation |
|---|---|
| **CDLI API rate limits** | Cache frequent identical queries in memory for 30 seconds (LRU cache on the server). |
| **LLM getting stuck in a tool loop** | Hard limit of 5 consecutive tool calls per user turn; a structured error is returned after that so the LLM can gracefully inform the user. |
| **Slow API responses** | Every CDLI fetch is wrapped in an `AbortController` with an 8-second timeout; the LLM is notified if a call times out. |
| **SSE connection drops** | The client widget auto-reconnects with exponential backoff. |
| **Overly long tool responses** | All tools return structurally paginated responses — a maximum of 20 results per call with a `next_page` cursor. `get_artifact` returns only key fields (`id`, `title`, `period`, `provenience`, `cdli_no`) by default; full transliteration is fetched separately via `get_translation` only when needed. This prevents malformed JSON from truncation. |

> 📎 **Visual**: Insert the **Complex Prompt Flow Diagram** (`complex_prompt_flow.html`) here — shows how the agent loop works and when it decides to call more tools vs. stop and respond.

---

### 5.5. Testing Strategy & Latency Validation

Testing happens at three levels:

**Unit Tests (per tool)**: Every MCP tool handler will be tested with `Vitest` using mocked CDLI API responses, checking that inputs are validated, outputs are formatted correctly, and edge cases (empty results, invalid IDs) are handled cleanly.

**Integration Tests (transport layer)**: The official MCP Inspector tool will be used to test the live SSE endpoint, verifying that tool schemas are correctly advertised and that every response conforms to the MCP protocol spec.

**End-to-End Tests (full stack)**: A set of pre-defined researcher queries (e.g., *"Find tablets from Nippur in Sumerian"*) will be run against the live server to validate:
- Search results returned in **under 2 seconds**.
- Translation fetch returned in **under 3 seconds**.
- Citation cards rendered correctly in the widget for every returned artifact.

Latency is measured using timing wrappers around every tool call that log response time to the console, making it easy to spot regressions during development.

---

### 5.6. Deployment

→ The MCP server will be packaged with a `Dockerfile` and `docker-compose.yml` for one-command deployment on any cloud host.

→ The React widget compiles to a static JS bundle that is dropped into the existing CakePHP site with a single `<script>` tag — no backend changes needed.

→ External researchers can connect to the hosted server from their desktop AI tools (Claude Desktop, Cursor) using just the public URL — no installation required on their end.

→ Deployment Strategy:

| Component | Platform |
|---|---|
| CDLI MCP Server | CDLI Infrastructure / Docker on VPS (e.g. Hetzner, DigitalOcean) |
| AI Research Widget (frontend) | Served as a static file from CDLI's own hosting |
| External client access | Public SSE endpoint (e.g. `mcp.cdli.earth`) |

