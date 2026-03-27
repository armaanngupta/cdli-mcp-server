# GSoC Proposal — Critique Analysis & Improvement Plan

> **File:** `final_draft_citique.txt`  
> **Proposal:** AI Research Interface for CDLI with MCP  
> **Reviewed by:** Antigravity  
> **Date:** 2026-03-21

---

## Part 1 — What the Critique Got Right (Strengths Confirmed ✅)

The reviewer explicitly called out four things as solid and not needing changes. These are safe to keep as-is.

| Strength | Why It Works |
|----------|-------------|
| **BYOM Architecture** | Letting users bring their own LLM API keys means CDLI pays nothing for LLM inference. Smart for an NGO. |
| **Dual Transport (STDIO + SSE)** | One codebase serving both desktop-power-users (STDIO) and casual web users (SSE widget). Clean design. |
| **Tool Schema Definition** | Using the official MCP TypeScript SDK and proper JSON Schema means any MCP client can call your tools without custom adapters. |
| **AbortController + 5-call limit** | Shows you anticipated LLM failure modes (infinite loops, hanging requests). Reviewer liked this. |

---

## Part 2 — Valid Critiques Explained

All six critiques raised are **valid and serious**. Here is what each means in plain language, and why the reviewer flagged it.

---

### 🔴 Critique 1 — The `/paper` Command Has No Real Architecture

**What the proposal says:**  
> "Built-in slash commands like `/paper <topic>` to trigger multi-step agent research loops."

**What the reviewer means:**  
You mentioned `/paper` as a feature but gave zero explanation of *how* it works. Writing a research paper from cuneiform database results is an extremely hard problem:

- The LLM needs to read through potentially hundreds of artifact transliterations.
- Each artifact can be thousands of tokens. 50 tablets × a few thousand tokens each = the entire context window explodes.
- A simple "chat completion loop" inside a browser widget cannot handle this — browsers have memory limits, streamed responses can freeze tabs, and the user's API key likely has token-per-minute limits.

**Why this is valid:** You listed this as a deliverable (Week 9–10) but provided no design for it. A reviewer or mentor would immediately ask *"how does this actually work?"* and you currently have no answer.

---

### 🔴 Critique 2 — The CQP Query Timeout is Too Aggressive

**What the proposal says:**  
> "AbortController timeouts (8s) to prevent LLM hanging."

**What the reviewer means:**  
The CQP-to-RDF system is described by CDLI's own mentors as **experimental**. Graph database queries (RDF/SPARQL style) are notoriously slow — a complex linguistic corpus query can legitimately take 20–30 seconds. Your blanket 8-second timeout will kill valid, non-trivial queries before they finish.

Additionally, you have no strategy for **long-polling** — a pattern where the server says "your query is running, check back in a moment" instead of holding the connection open indefinitely. Without this, complex CQP queries will always fail for the end user.

**Why this is valid:** The 8-second limit was designed for REST API calls, not for graph queries. Applying it uniformly without exception handling is a real bug.

---

### 🔴 Critique 3 — Trimming JSON Responses Will Break the LLM

**What the proposal says:**  
> "Tool output is trimmed before being fed back to the LLM."

**What the reviewer means:**  
If an API returns a large JSON object and you just cut it at some character limit, you produce **malformed JSON** — e.g., a truncated `]}` that closes nothing. When the LLM tries to parse this, it either:
- Fails entirely with a parse error, or
- **Hallucinates** the missing data (makes up artifact IDs, dates, or text).

Both outcomes are terrible. The only correct solutions are:
1. **Structural pagination** — query the API for page 1 of results, return only page 1 in a valid JSON wrapper, and let the LLM ask for page 2.
2. **Key subsetting** — return only the most important fields (ID, title, period) and let the LLM call `get_artifact` for the full record.

**Why this is valid:** This is not a minor oversight — it is a correctness bug that will cause the LLM to produce wrong answers.

---

### 🔴 Critique 4 — In-Memory Caching is Useless for LLM Queries

**What the proposal says:**  
> "In-memory 30s TTL caching for repeated identical agent queries."

**What the reviewer means:**  
Caching only works when the same *exact* query string hits the cache. LLMs never generate the same string twice — they rephrase. `"rain rituals"` vs `"rituals about rain"` vs `"rain-related ceremonies"` are semantically identical but will all cache-miss every time.

Worse: holding this cache in memory inside a Node.js container **breaks horizontal scaling**. If you spin up two containers (for load), they each have their own cache and share no state. This makes the cache pointless.

The real solution is a **semantic cache** — store embeddings of past queries and find the nearest neighbour, so semantically similar queries return cached results. Redis with vector search is the standard tool for this.

**Why this is valid:** The current caching proposal provides near-zero benefit in practice and actively hurts scalability.

---

### 🔴 Critique 5 — SSE Won't Scale to Real Concurrent Load

**What the proposal says:**  
> "Protocol: We will use Server-Sent Events (SSE) via Express."

**What the reviewer means:**  
SSE keeps an HTTP connection open for the duration of a session. Node.js has a limit on open file descriptors (often 1024 by default). If 100 students from a university class open the widget simultaneously, you will hit this limit quickly. The event loop also gets saturated managing hundreds of open connections.

A single Docker container with no tuning will not survive this load. The proposal has no mention of:
- Connection limits
- Load balancing strategy
- Graceful degradation

**Why this is valid:** This is a real-world deployment concern, especially for an academic tool that could see bursty usage (conference days, class assignments, etc.).

---

### 🔴 Critique 6 — CakePHP Integration is More Complex Than One `<script>` Tag

**What the proposal says:**  
> "A single script inclusion in the global layout footer... This ensures the widget persists across page navigations without modifying the core PHP controllers."

**What the reviewer means:**  
Embedding a modern React bundle (built with Vite, using ESModules) into a legacy CakePHP monolith is non-trivial. The proposal ignores three real problems:

1. **Content Security Policy (CSP):** The CDLI web server almost certainly has HTTP headers that block external JavaScript or cross-origin connections. Your `mcp.cdli.earth` SSE connection will be blocked by the browser unless CSP is updated — a server-side change.
2. **CSS Pollution:** React component styles can leak into the global page namespace and break existing CDLI styling (or vice versa). Shadow DOM or strict CSS scoping is needed.
3. **CORS:** The widget makes browser-based SSE calls to `mcp.cdli.earth`. The MCP server must have CORS headers exactly right or the browser will block the connection.

**Why this is valid:** This is not a "talk less, show more" situation — it is a "you did not account for real integration constraints" situation.

---

## Part 3 — Verdict: Are All Critiques Valid?

**Yes, all six critiques are valid.** The critique is technically rigorous and fair. The strengths section is also accurate — the reviewer is not being unreasonable, they are pointing out gaps between what the proposal *claims* and what it *actually specifies*. The premortem scenario at the end is a plausible failure mode if the gaps are not addressed.

---

## Part 4 — Improvement Plan

Here is a concrete plan to fix each issue in the proposal.

---

### Fix 1 — `/paper` Command: Define a Real Architecture

**Changes needed in proposal:**

- Remove the vague one-liner about slash commands.
- Add a dedicated subsection describing a **multi-step agentic pipeline** for `/paper`:
  1. **Discovery phase:** LLM calls `advanced_search` with the topic and collects artifact IDs (not full text).
  2. **Scoping phase:** LLM selects the top N most relevant artifacts (hard cap, e.g. N=10) based on metadata alone.
  3. **Ingestion phase:** LLM calls `get_artifact` for each of the N artifacts *sequentially*, summarizing each one before moving to the next (to avoid loading all of them into context simultaneously).
  4. **Synthesis phase:** LLM generates the paper outline + draft from the accumulated summaries.
- Note the tool-call limit (5 per agent turn, as already mentioned) and explain how the `/paper` workflow operates *across multiple turns* to stay within token limits.
- Acknowledge this is a GSoC stretch goal with a dedicated week buffer.

**Alternatively (simpler and more defensible):** Explicitly scope `/paper` down to a structured *bibliography + annotation* output (not a full paper draft), which is achievable within context limits.

---

### Fix 2 — CQP Query: Separate Timeout + Async Strategy

**Changes needed in proposal:**

- Apply the 8s timeout **only to REST API calls** (artifact retrieval, search).
- For `cqp_query`, implement a **job queue pattern**:
  - Request is submitted → server returns a `job_id` immediately.
  - LLM polls `get_job_status(job_id)` until complete or failed.
  - Timeout is set to 60s for the overall job, not 8s.
- Mention this explicitly in the performance & security section.

---

### Fix 3 — JSON Response Handling: Replace Trimming with Pagination

**Changes needed in proposal:**

- Remove "trimmed" from the mitigation strategy entirely.
- Replace with: **"All tool responses are structurally paginated. Tools return a maximum of 20 results per call with a `next_page` cursor. The LLM may call the tool again with the cursor to retrieve additional results."**
- For `get_artifact`, specify that only the key fields are returned by default (`id`, `title`, `period`, `provenience`, `cdli_no`), with a `full=true` parameter for complete transliteration text.

---

### Fix 4 — Caching: Acknowledge Limitations + Propose Better Strategy

**Changes needed in proposal:**

- Replace the "in-memory 30s TTL" description with: **"Parameter-level normalization before caching (e.g., lowercasing, stripping whitespace, sorting multi-value params) to maximize simple cache hit rates. For the pilot phase, this is sufficient. Post-GSoC, semantic caching via Redis with vector embeddings is the recommended upgrade path."**
- Remove the claim that this enables horizontal scaling — it does not, and the reviewer will catch it.
- For deployment, note that the Docker container is **stateless at the data layer** — the cache is an optimization, not a dependency.

---

### Fix 5 — SSE Scalability: Acknowledge + Add Mitigation

**Changes needed in proposal:**

- Add to the HTTP/SSE section: **"The Node.js process will be configured with `--max-connections` limits and the OS file descriptor limit raised (`ulimit -n 65536`) in the Docker container. Connection count will be monitored via a `/health` endpoint. For GSoC scope (low traffic, academic use), a single container is sufficient. The architecture is designed to add a load balancer in front of multiple replicas as a post-GSoC scaling step."**
- This shows you are aware of the limitation without over-engineering it for a GSoC project.

---

### Fix 6 — CakePHP Integration: Acknowledge Real Constraints

**Changes needed in proposal:**

- Replace the "one-liner" framing with a proper integration checklist:
  1. **CSP headers:** Update CDLI's nginx/Apache config to allow `connect-src mcp.cdli.earth`.
  2. **CORS:** MCP server Express config will whitelist `cdli.earth` as an allowed origin.
  3. **CSS Isolation:** Widget built with scoped CSS class prefixes (e.g., `cdli-ai-*`) to prevent global style collisions.
  4. **Bundle delivery:** Vite build outputs a self-contained `bundle.js`. A Week 11 task is dedicated specifically to integration testing in the CakePHP sandbox.
- This turns a weakness into a demonstration of thoroughness.

---

## Part 5 — Priority Order for Revision

| Priority | Critique | Effort to Fix in Proposal |
|----------|----------|--------------------------|
| 🔴 Critical | `/paper` architecture | Medium — needs a new subsection |
| 🔴 Critical | JSON trimming → pagination | Low — replace one sentence |
| 🔴 Critical | CakePHP integration details | Low — add a checklist |
| 🟡 High | CQP timeout → async job | Medium — add job queue pattern |
| 🟡 High | SSE scalability acknowledgement | Low — add one paragraph |
| 🟡 Medium | Caching strategy clarification | Low — reframe the claim |

---

*The proposal has a strong foundation. These fixes are about closing the gap between what is claimed and what is designed. A revised proposal addressing all six points would be significantly harder to critique.*
