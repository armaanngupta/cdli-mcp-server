GSoC Proposal for
AI Research Interface for CDLI with MCP

Armaan Gupta


Abstract

This proposal outlines the development of an AI Research Interface for the Cuneiform Digital Library Initiative (CDLI) using the Model Context Protocol (MCP), enabling natural language interaction with one of the world's largest cuneiform text archives. The project will implement an MCP-compliant server with TypeScript and Node.js, an AI Research Workspace — a browser-based standalone application with Bring Your Own Model (BYOM) support — and an AI Search entry point integrated into the CDLI website. This will make CDLI's rich corpus of ancient tablets accessible to scholars, linguists, and students through conversational AI, while also enabling integration with third-party AI clients like Claude Desktop. The system will additionally support CQP-based linguistic corpus queries and an AI-assisted research paper generation agent with automatic artifact citations.


1    Personal Details

●  Name: Armaan Gupta
●  University: [Your University]
●  Email: [Your Email]
●  GitHub: github.com/armaanngupta
●  Instant Messaging: [WhatsApp / Email]
●  Country of Residence: India
●  Timezone: IST (GMT + 0530)
●  Primary Language: English


2    Introduction

I am Armaan Gupta from India, currently pursuing [Your Degree] at [Your University]. I have [X] years of experience building full-stack applications and AI-integrated tools. I am well versed in TypeScript, Node.js, React, and REST API integration.

I have been following the CDLI project with genuine academic interest in ancient Near Eastern history and digital humanities. The intersection of AI tooling and historical text archives is something I find uniquely compelling — this project would let me contribute meaningfully to both fields at once.

I have already built a working proof-of-concept MCP server for CDLI, which can be found at github.com/armaanngupta/cdli-mcp-server. The prototype was built to understand the MCP SDK's tool registration model, the CDLI API's response formats, and the stdio/HTTP transport mechanisms. It demonstrates my ability to navigate the project's technical foundations. The full production implementation will be built as part of this GSoC project, designed from the ground up with proper architecture, testing, and documentation.

When I am not coding, I enjoy [your hobbies — e.g., reading about ancient history, hiking, etc.].


3    Background

CDLI hosts nearly 400,000 cuneiform tablet records spanning thousands of years of human history — administrative texts, literary compositions, legal documents, astronomical records, and more. Yet accessing this data today requires technical familiarity with structured forms, field names, and advanced search syntax. For a researcher who simply wants to know "what tablets mention grain distribution in Ur III Nippur", the path from question to answer involves many manual steps.

With the rapid rise of LLMs and AI agents, and the standardization of the Model Context Protocol (MCP), there is now a clear path to solve this accessibility problem. An MCP server exposing CDLI capabilities as structured tools allows any MCP-compatible AI client to discover and invoke artifact searches, retrieve metadata, execute linguistic corpus queries, and even draft research papers — all from a natural language conversation.

Implementing an MCP server also ensures that CDLI data is reachable from third-party tools such as Claude Desktop, Cursor, and Windsurf. The BYOM design means CDLI does not bear LLM API costs — users bring their own keys.


4    Description of Work

4.1. Research and Architecture Design

1.  Study the existing CDLI API, codebase, and search infrastructure thoroughly
2.  Study the CQP-to-RDF project (https://cdli.earth/cqp4rdf/) and understand its API interface
3.  Map all query parameters from the Advanced Search page (https://cdli.earth/search/advanced)
4.  Research and configure HTTP/SSE transport using the MCP TypeScript SDK
5.  Finalize the full list of tools and their schemas

4.2. Core MCP Server Development

4.2.1 MCP Server Tool Design

Define and implement all tool schemas following a modular structure where each tool lives in its own folder (src/tools/<tool-name>/index.ts) and exports: name, description, inputSchema, and handler. This design keeps tools fully independent and trivially extensible.

Key tools to implement:

●  search_artifacts — keyword/phrase search across the CDLI corpus
●  advanced_search — structured search using all fields from /search/advanced (language, genre, period, provenience, artifact_type, translation_text, museum_no, publication, date)
●  get_artifact — full artifact metadata including inline ATF inscription text, returning a standardized citation
●  get_translation — lightweight extraction of ATF translation text only, without the full metadata payload
●  cqp_query — CQP linguistic corpus queries via the cdli.earth/cqp4rdf/ API
●  get_authors — list of CDLI authors (with pagination)
●  get_publications — list of publications (with pagination)
●  get_provenience — list of archaeological find sites (with pagination)
●  ping — server liveness check

The following is an example pseudo-implementation illustrating the planned tool structure across the three categories:

    // ── Artifact Tools ──

    export const get_artifact: Tool = {
      name: "get_artifact",
      description: "Retrieve full metadata for a CDLI artifact by ID, including ATF inscription text.",
      inputSchema: { id: string("CDLI artifact ID, e.g. P315278") },
      handler: async ({ id }) => {
        const data = await fetchCDLI(`/artifacts/${normalizeId(id)}.json`);
        return formatCitation(data); // "P{id} — {designation}\nhttps://cdli.earth/artifacts/{id}"
      }
    };

    export const get_translation: Tool = {
      name: "get_translation",
      description: "Return only the ATF inscription text for a given artifact.",
      inputSchema: { id: string("CDLI artifact ID") },
      handler: async ({ id }) => {
        const data = await fetchCDLI(`/artifacts/${normalizeId(id)}.json`);
        return data.inscription.atf;
      }
    };

    // ── Search Tools ──

    export const search_artifacts: Tool = {
      name: "search_artifacts",
      description: "Keyword search across the CDLI corpus.",
      inputSchema: { query: string, limit?: number, offset?: number },
      handler: async ({ query, limit = 20, offset = 0 }) => {
        const results = await fetchCDLI(`/search.json?query=${query}&limit=${limit}&offset=${offset}`);
        return results.map(formatCitation).join("\n\n");
      }
    };

    export const advanced_search: Tool = {
      name: "advanced_search",
      description: "Structured search using multiple CDLI corpus fields.",
      inputSchema: {
        language?: string,   // e.g. "Sumerian", "Akkadian"
        genre?: string,      // e.g. "administrative", "literary"
        period?: string,     // e.g. "Ur III", "Old Babylonian"
        provenience?: string,// e.g. "Nippur", "Ur"
        translation_text?: string,
        limit?: number, offset?: number
      },
      handler: async (args) => {
        const params = buildQueryParams(args);
        const results = await fetchCDLI(`/search.json?${params}`);
        return results.map(formatCitation).join("\n\n");
      }
    };

    export const cqp_query: Tool = {
      name: "cqp_query",
      description: "Run a CQP linguistic corpus query against the CDLI corpus.",
      inputSchema: { expression: string("CQP expression, e.g. [lemma='rain']") },
      handler: async ({ expression }) => {
        const results = await fetchCQPtoRDF(expression);
        return results.map(formatCitation).join("\n\n");
      }
    };

    // ── List Tools (get_authors, get_publications, get_provenience follow the same pattern) ──

    export const get_authors: Tool = {
      name: "get_authors",
      description: "List CDLI authors with pagination.",
      inputSchema: { limit?: number, offset?: number },
      handler: async ({ limit = 20, offset = 0 }) => {
        return await fetchCDLI(`/authors.json?limit=${limit}&offset=${offset}`);
      }
    };

    // ping: returns server status and timestamp

4.2.2 Artifact Citation Standard

All tools that return artifact results will follow a mandatory citation format to ensure scholarly traceability:

    P254876 — Rain invocation ritual
    https://cdli.earth/artifacts/254876

This will be enforced across search_artifacts, advanced_search, get_artifact, and get_translation.

4.2.3 Pagination Support

All list-returning tools (get_authors, get_publications, get_provenience, search_artifacts, advanced_search) will accept limit (default 20) and offset (default 0) parameters, enabling agents to page through large result sets efficiently.

4.2.4 CQP-to-RDF Tool Integration

The CQP-to-RDF system exposes a linguistic corpus query interface at cdli.earth/cqp4rdf/. The cqp_query tool will:
1.  Accept a CQP expression string, e.g. [lemma="rain"]
2.  Call the relevant CQP-to-RDF API endpoint
3.  Parse the RDF or JSON response into artifact references
4.  Return artifact citation links

4.3. HTTP/SSE Transport

The MCP server will support two transport modes. The stdio transport enables integration with desktop AI clients such as Claude Desktop. For the browser-based AI Research Workspace to connect, an HTTP/SSE transport will be implemented in parallel:

1.  Install Express: npm install express @types/express
2.  Create src/http-server.ts using SSEServerTransport from the MCP SDK
3.  Register the same tools as the stdio entry point
4.  Add CORS headers for cross-origin browser requests
5.  Add rate limiting via express-rate-limit
6.  Expose on a configurable PORT (default 3000)
7.  Create a Dockerfile for containerized deployment

REST Endpoints (MCP over HTTP/SSE):
●  GET  /sse           — establishes the SSE stream for MCP communication
●  POST /message       — JSON-RPC message endpoint

4.4. AI Research Workspace (MCP Client and Agent Service)

A standalone React + TypeScript SPA (Vite) that acts as the MCP client, connecting to the CDLI MCP server over HTTP/SSE and running the full LLM agent loop in the browser.

1.  Create an MCP client service that connects to the CDLI MCP server via HTTP/SSE and discovers all available tools at startup
2.  Expose a method for the chat interface to pass in user queries along with the full conversation history for context
3.  Add conversation history management so that prior exchanges are included in each LLM call, enabling multi-turn research sessions
4.  Add a system prompt that instructs the LLM to: always cite artifacts in the standard CDLI citation format, prefer structured tool calls over direct responses when querying data, and ask the user for clarification when required parameters are missing
5.  Implement the tool-calling agent loop — the LLM receives the user query and the list of available tools, decides which tools to call and in what order, executes them via the MCP server, and feeds the results back to the LLM for a final response
6.  Support multi-provider LLM integration (OpenAI, Anthropic Claude, Google Gemini, Mistral AI), each wrapped behind a common interface so the agent loop is fully provider-agnostic. The user supplies their own API key via the settings panel, stored only in the browser's localStorage
7.  Stream the LLM's response token-by-token to the frontend using the provider's streaming API
8.  Build the chat UI around this agent service: a session sidebar, markdown-rendered message area, inline artifact citation cards for tool results, slash commands (/search, /artifact, /cqp, /paper), and a settings panel for API key and LLM provider configuration
9.  [Optional] Support voice-to-text input using the Web Speech API

4.5. Research Paper Generation Agent

An agentic workflow triggered by /paper or a natural language request:

1.  User provides a research topic (e.g. "rain rituals in Old Babylonian texts")
2.  Agent calls advanced_search with relevant parameters
3.  Agent calls get_translation for the top N results
4.  Agent clusters results by theme (period, genre, language)
5.  Agent generates a structured academic paper:
    ●  Abstract
    ●  Introduction
    ●  Corpus Overview (table of artifacts)
    ●  Textual Evidence (translation excerpts)
    ●  Discussion
    ●  References (all formatted as CDLI artifact citation links)
6.  Export: Markdown copy / file download

4.6. AI Search Button on cdli.earth

A targeted change to the CakePHP frontend:
●  Adds an "AI Search" button below the existing "Corpus Search" section
●  On click, opens the AI Research Workspace in a new browser tab
●  Minimal risk — confined to a single PHP template change

4.7. Performance Strategy

The system must meet strict latency requirements — artifact retrieval under 2 seconds and search response under 3 seconds. These will be achieved as follows:

●  Artifact retrieval: The get_artifact tool makes a single direct fetch to cdli.earth/artifacts/{id}.json — no joins or server-side computation. A co-hosted server will have a sub-500ms round-trip to cdli.earth, leaving ample budget for JSON parsing and MCP serialization.

●  Search latency: The advanced_search and search_artifacts tools pass queries directly to the CDLI search API with no added computation. An in-memory response cache with a short TTL (30 seconds) will be added to absorb repeated identical queries within a single agent session, which is common in agentic loops.

●  Streaming: The HTTP/SSE transport streams LLM tokens to the browser as they arrive, so the user sees output immediately — perceived latency is far lower than total generation time.

●  Timeout fallback: All fetch calls will be wrapped with an AbortController timeout (default 8s). If the upstream CDLI API does not respond in time, the tool returns a structured error rather than hanging the agent indefinitely.

4.8. Testing and Integration

1.  Unit tests for each MCP tool handler (Vitest)
2.  Integration tests: run MCP Inspector against the live server and verify all tools return valid responses
3.  End-to-end test: AI Research Workspace makes a full multi-tool research pipeline query
4.  Performance validation: confirm artifact retrieval < 2s and search < 3s under normal conditions
5.  Security review: API key handling (localStorage only), prompt sanitization, rate limiting

4.8. Documentation and Release

1.  Complete README for the MCP server and all tools
2.  Developer guide: how to add new tools (one folder = one tool)
3.  User guide for the AI Research Workspace: how to add API keys, use slash commands, export papers
4.  List MCP server integration instructions for third-party clients (Claude Desktop, Cursor, etc.)


5    Proposed Frontend UI

The frontend will be a modern chat interface with a sidebar for session history, a main message area with inline artifact citation cards, a settings popup for LLM/API key configuration, and slash command support.

Figure 1: Main Chat UI — left sidebar for sessions, main area for conversation, artifact citation cards inline in responses, chat input at bottom with slash command support.

Figure 2: Settings Popup — LLM provider dropdown (OpenAI, Anthropic, Gemini, Mistral), API key field, theme toggle.


6    Project Module Structure (Tentative)

cdli-mcp-server/
├── src/
│   ├── index.ts                    # stdio MCP server entry point
│   ├── http-server.ts              # HTTP/SSE MCP server entry point
│   └── tools/
│       ├── index.ts                # barrel export of all tools
│       ├── get-artifact/index.ts
│       ├── search-artifacts/index.ts
│       ├── advanced-search/index.ts
│       ├── get-translation/index.ts
│       ├── cqp-query/index.ts
│       ├── get-authors/index.ts
│       ├── get-publications/index.ts
│       ├── get-provenience/index.ts
│       └── ping/index.ts
├── Dockerfile
├── docker-compose.yml
├── package.json
└── tsconfig.json

cdli-ai-workspace/                  # frontend SPA
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── InputBar.tsx
│   │   │   └── ArtifactCitationCard.tsx
│   │   ├── Sidebar/
│   │   │   ├── SessionList.tsx
│   │   │   └── NewChatButton.tsx
│   │   └── Settings/
│   │       └── SettingsModal.tsx
│   ├── services/
│   │   ├── mcpClient.ts            # connects to CDLI MCP server via HTTP/SSE
│   │   ├── llmProviders/
│   │   │   ├── openai.ts
│   │   │   ├── anthropic.ts
│   │   │   ├── gemini.ts
│   │   │   └── mistral.ts
│   │   └── agentLoop.ts           # tool-calling loop and paper generation
│   └── hooks/
│       └── useConversation.ts
└── package.json


7    Results for the CDLI Community

This project will deliver significant value to the CDLI community by making the world's largest cuneiform archive accessible through natural language. Scholars will no longer need to know advanced query syntax or field names — they can simply ask in plain language. Linguists can run CQP corpus queries through conversation. Graduate students can generate preliminary research paper drafts with automatic artifact citations in minutes. And because the MCP server is publicly accessible, any AI tool that supports MCP can be configured to query CDLI — expanding CDLI's reach far beyond its current user base.

CDLI will become the first AI-native digital humanities archive.


8    Deliverables

1.  CDLI MCP server with all tools (search_artifacts, advanced_search, get_artifact, get_translation, cqp_query, get_authors, get_publications, get_provenience, ping) with pagination and artifact citation standard
2.  HTTP/SSE transport for the MCP server with Docker support
3.  AI Research Workspace (React SPA) with multi-LLM BYOM support
4.  Research Paper Generation Agent
5.  AI Search button integrated into cdli.earth
6.  Comprehensive test suite for all tools
7.  User and developer documentation


9    Timeline

9.1   Week 1
Study the CDLI codebase, API infrastructure, and existing search systems. Research MCP SDK options and transport mechanisms. Document all key operations to be exposed as tools. Finalize design decisions after community discussion.

9.2   Week 2–3
Set up the MCP server project from scratch. Define the modular tool structure and implement core artifact retrieval and search tools. Add the artifact citation standard to all tools. Write unit tests for each tool.

9.3   Week 4–5
Implement remaining tools — structured multi-field search, translation extraction, and the linguistic corpus query tool. Add pagination support across all list-returning tools.

9.4   Week 6
Add HTTP/SSE transport alongside stdio. Handle CORS, rate limiting, and timeout fallbacks. Containerize the server with Docker. Verify browser connectivity.

9.5   Week 7–8
Bootstrap the AI Research Workspace frontend. Connect the frontend to the MCP server over HTTP/SSE.

9.6   Week 9–10
Implement multi-provider LLM integration and streaming responses. Enhance the frontend. Design and implement the research paper generation agent with structured output and export.

9.7   Week 11
Integrate the AI Search entry point into the CDLI website. Run end-to-end tests across the full pipeline. Validate performance targets and conduct a security review.

9.8   Week 12
Finalize all documentation — server, workspace, user guide, and contributor guide. Incorporate review feedback. Prepare final GSoC submission.


10    Community Engagement

1.  Regular updates on the CDLI developer mailing list and GitHub Discussions
2.  Weekly sync with mentors throughout the project
3.  Beta testing session with CDLI community members and scholars before final submission
4.  Monitoring new issues and contributing fixes that fall within this project's scope
5.  Remaining active as a contributor post-GSoC — the AI tooling ecosystem around CDLI will continue to grow


11    References

1.  CDLI MCP Server Prototype (my repo): https://github.com/armaanngupta/cdli-mcp-server
2.  MCP TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
3.  MCP Build a Server Guide: https://modelcontextprotocol.io/docs/develop/build-server
4.  Introduction to MCP (Anthropic): https://anthropic.skilljar.com/introduction-to-model-context-protocol
5.  mcp-open-library (reference architecture): https://github.com/8enSmith/mcp-open-library
6.  CDLI Advanced Search: https://cdli.earth/search/advanced
7.  CDLI CQP-to-RDF: https://cdli.earth/cqp4rdf/


** All supplementary materials — including UI mockup screenshots and the working prototype — are available at: github.com/armaanngupta/cdli-mcp-server
