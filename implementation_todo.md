# CDLI AI Research Interface — Implementation TODO

## Phase 1: MCP Server — Tool Expansion

### 1.1 Advanced Search Tool
- [ ] **Study Advanced Search endpoint**
  - Analyze all query parameters available at `https://cdli.earth/search/advanced`
  - Map each field (language, genre, period, provenience, artifact_type, translation_text, museum_no, publication, etc.) to its corresponding API query param
- [ ] **Implement `advanced_search` tool**
  - Tool accepts any combination of the above fields as optional inputs
  - Constructs the correct query string for `https://cdli.earth/search.json?<params>`
  - Returns results in the artifact citation format: `P254876 — Title\nhttps://cdli.earth/artifacts/254876`
- [ ] **Add pagination support (`limit` + `offset`)**
  - All list-returning tools should accept `limit` (default 20) and `offset` (default 0)
  - Allows agents to page through large result sets

### 1.2 Translation Extraction Tool
- [ ] **Implement `get_translation` tool**
  - Takes an artifact ID (accepting both `P315278` and `315278` formats)
  - Returns only the `atf_translation_text` field from the artifact's JSON response
  - Lighter than `get_artifact` — useful when the agent only needs the text portion

### 1.3 CQP-to-RDF Tool
- [ ] **Study the CQP-to-RDF project**
  - Read documentation at `https://cdli.earth/cqp4rdf/`
  - Understand the API endpoint it exposes and what query syntax it accepts (CQP: `[lemma="rain"]`)
  - Understand what the RDF response contains and how to parse it into artifact references
- [ ] **Implement `cqp_query` tool**
  - Accepts a CQP expression string
  - Calls the CQP-to-RDF API endpoint
  - Returns matching artifact IDs and citation links

### 1.4 Artifact Citation Standard
- [ ] **Enforce citation format across all tools**
  - Every tool that returns artifact results must format them as:
    ```
    P254876 — Rain invocation ritual
    https://cdli.earth/artifacts/254876
    ```
  - Update `search_artifacts`, `advanced_search`, `get_artifact`, `get_translation` to include this in their output

### 1.5 Existing Tool Improvements
- [ ] **Add `limit` + `offset` to `get_authors`**
- [ ] **Add `limit` + `offset` to `get_publications`**
- [ ] **Add `limit` + `offset` to `get_provenience`**
- [ ] **Add `limit` + `offset` to `search_artifacts`**

---

## Phase 2: MCP Server — HTTP/SSE Transport

### 2.1 Add HTTP/SSE Server Entry Point
- [ ] **Install Express**
  - `npm install express @types/express`
- [ ] **Create `src/http-server.ts`**
  - Uses `SSEServerTransport` from the MCP SDK instead of `StdioServerTransport`
  - Starts an Express server (default port 3000 or configurable via `PORT` env var)
  - Registers the same tools as the stdio server
- [ ] **Update `package.json` scripts**
  - Add `"start:http": "node build/http-server.js"` for web mode
  - Keep `"start"` as stdio mode for Claude Desktop compatibility
- [ ] **Handle CORS headers**
  - The browser-based frontend will call from a different origin — must set `Access-Control-Allow-Origin`

### 2.2 Docker Support
- [ ] **Create `Dockerfile`**
  - Base image: `node:20-alpine`
  - Builds TypeScript, runs `start:http`
  - Exposes port 3000
- [ ] **Create `docker-compose.yml`** (optional)
  - Service for the MCP server
  - Service for the frontend (if serving statically)

---

## Phase 3: AI Research Workspace (Frontend)

### 3.1 Project Setup
- [ ] **Bootstrap React app (or Vite + React)**
  - `npx create-vite@latest cdli-ai-workspace -- --template react-ts`
  - Or create a plain `index.html` + vanilla JS if keeping it lightweight
- [ ] **Install dependencies**
  - MCP client SDK (if available for browsers, else use raw HTTP/SSE fetch)
  - OpenAI SDK, Anthropic SDK (for BYOM support)
  - Marked / react-markdown (for rendering AI responses as markdown)

### 3.2 Settings Panel
- [ ] **LLM Provider dropdown**
  - Options: OpenAI, Anthropic, Google Gemini, Mistral AI
- [ ] **API Key input field**
  - Password-masked input
  - Stored in `localStorage` — never sent to the CDLI server
- [ ] **Save / Cancel buttons**
- [ ] **Theme toggle** (Light / Dark / System)

### 3.3 Chat Interface
- [ ] **Sidebar — Session management**
  - "New Chat" button
  - List of recent chat session titles
  - Sessions persisted in `localStorage`
- [ ] **Main chat area**
  - Display user messages and AI responses in alternating bubbles
  - Render AI responses as markdown (support **bold**, lists, code blocks)
  - Render artifact citations as styled clickable cards:
    ```
    ┌─────────────────────────────┐
    │ P254876                     │
    │ Rain invocation ritual      │
    │ cdli.earth/artifacts/254876 │
    └─────────────────────────────┘
    ```
- [ ] **Message input bar**
  - Text input field
  - Send button
  - Slash command support (`/search`, `/getArtifact P315278`, `/cqp [lemma="rain"]`)
- [ ] **Streaming response display**
  - Show AI response token-by-token as it arrives (streaming mode)

### 3.4 MCP Client Integration
- [ ] **Connect to CDLI MCP Server via HTTP/SSE**
  - On user message, the frontend calls the LLM with the MCP tools exposed in the system prompt
  - LLM returns tool call → frontend invokes MCP server HTTP endpoint → result returned to LLM → final response shown
- [ ] **Tool call display**
  - Show an indicator while a tool is being called (e.g., "🔍 Searching artifacts...")

---

## Phase 4: Research Paper Generation Agent

### 4.1 Agent Workflow
- [ ] **Design the agent loop**
  - User provides topic: genre / period / language / keyword
  - Agent calls `advanced_search` with appropriate parameters
  - Agent calls `get_translation` for top N artifacts
  - Agent clusters results thematically
  - Agent writes structured academic paper draft

### 4.2 Paper Output Format
- [ ] **Structured sections**
  - Abstract
  - Introduction
  - Corpus Overview (table of matching artifacts)
  - Textual Evidence (translation excerpts)
  - Discussion
  - References (all CDLI citation links)
- [ ] **Export options**
  - Copy to clipboard as Markdown
  - Download as `.md` file (stretch goal: PDF export)

---

## Phase 5: CDLI Website Integration

### 5.1 "AI Search" Button on cdli.earth
- [ ] **Clarify scope with mentor**
  - Confirm whether adding a button to the CakePHP frontend is in GSoC scope
- [ ] **Add button in CakePHP template**
  - Location: below "Corpus Search" on `https://cdli.earth`
  - Label: "AI Search"
  - Action: opens the AI Research Workspace URL in a new tab

---

## Phase 6: Non-Functional Requirements

### 6.1 Performance
- [ ] Artifact retrieval < 2 seconds — verify with timing logs
- [ ] Search latency < 3 seconds

### 6.2 Reliability
- [ ] Graceful error handling in all tools (API down, 404, malformed response)
- [ ] Fallback message when LLM fails or API key is invalid

### 6.3 Security
- [ ] API keys never leave the browser (stored in `localStorage`, not sent to MCP server)
- [ ] Rate limiting on the MCP HTTP server (use `express-rate-limit`)
- [ ] Sanitize all inputs before constructing API query strings

### 6.4 Testing
- [ ] Unit tests for each MCP tool handler
- [ ] Integration test: run MCP Inspector against the server and verify all tools return valid responses
- [ ] End-to-end test: Claude Desktop or the workspace UI makes a full research query

---

## Current Status

| Feature | Status |
|---|---|
| MCP server base structure | ✅ Done |
| `get_artifact` tool | ✅ Done |
| `search_artifacts` tool | ✅ Done |
| `get_authors` tool | ✅ Done |
| `get_publications` tool | ✅ Done |
| `get_provenience` tool | ✅ Done |
| `ping` tool | ✅ Done |
| Artifact citation format | ⬜ Not yet enforced |
| `advanced_search` tool | ⬜ Not started |
| `get_translation` tool | ⬜ Not started |
| `cqp_query` tool | ⬜ Not started |
| Pagination on all tools | ⬜ Not started |
| HTTP/SSE transport | ⬜ Not started |
| AI Research Workspace UI | ⬜ Not started |
| Research Paper Agent | ⬜ Not started |
| CDLI website button | ⬜ Pending mentor confirmation |
