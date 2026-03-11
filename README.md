# CDLI MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes [CDLI (Cuneiform Digital Library Initiative)](https://cdli.mpiwg-berlin.mpg.de/) data as structured tools for AI agents.

This prototype connects directly to the CDLI public API and allows any MCP-compatible client (like Claude Desktop) to search artifacts, retrieve metadata, fetch authors, and more — without any custom integration work.

> **Transport:** `stdio` (standard input/output)

---

## Project Structure

```
cdli-mcp-server/
├── src/
│   ├── index.ts              # MCP server entry point
│   └── tools/
│       ├── index.ts          # Barrel export of all tools
│       ├── get-artifact/
│       │   └── index.ts      # Fetch a single artifact by ID
│       ├── get-authors/
│       │   └── index.ts      # List CDLI authors
│       ├── search-artifacts/
│       │   └── index.ts      # Full-text artifact search
│       ├── get-publications/
│       │   └── index.ts      # List publications
│       ├── get-provenience/
│       │   └── index.ts      # List proveniences (find sites)
│       └── ping/
│           └── index.ts      # Liveness check
├── build/                    # Compiled JS output (git-ignored)
├── package.json
└── tsconfig.json
```

---

## Prerequisites

- [Node.js](https://nodejs.org/) v18 or higher
- npm

---

## Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd cdli-mcp-server

# 2. Install dependencies
npm install

# 3. Build the TypeScript source
npm run build
```

To rebuild and run in one step during development:
```bash
npm run dev
```

---

## Testing the Server

### Option 1: MCP Inspector (Recommended)

The official MCP Inspector gives you a browser UI to list and call tools interactively.

**Step 1:** Build the server first (must be done every time you change source files):
```bash
npm run build
```

**Step 2:** Launch the inspector with the compiled server:
```bash
npx @modelcontextprotocol/inspector node build/index.js
```

> ⚠️ **Do NOT use `npm run dev` as the inspector command.** The `dev` script prints build output to stdout, which corrupts the JSON-RPC stream and causes `SyntaxError: Unexpected token '>'` errors.

**Step 3:** The inspector will print a URL like:
```
🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<your-token>
```

**Step 4:** Open that **full URL** (including the token query parameter) in your browser. On WSL/Linux the browser won't auto-open, so copy-paste it manually.

> 💡 **Tip:** To skip the auth token entirely for local development, use:
> ```bash
> DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector node build/index.js
> ```
> Then navigate to `http://localhost:6274` without any token.

**Step 5:** In the inspector UI:
- Set **Transport** to `STDIO`
- Set **Command** to `node`
- Set **Args** to `build/index.js`
- Click **Connect**

You can now list all tools and call them with a form-based interface.

### Option 2: Raw JSON-RPC via stdin

Since the server uses stdio transport, you can pipe raw JSON-RPC messages directly:

**List all available tools:**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node build/index.js
```

**Call `get_artifact` with artifact ID `P315278`:**
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_artifact","arguments":{"id":"P315278"}}}' | node build/index.js
```

**Call `search_artifacts`:**
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_artifacts","arguments":{"query":"Ur III tablet"}}}' | node build/index.js
```

---

## Connecting to Claude Desktop

1. Build the server first: `npm run build`

2. Find your Claude Desktop config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

3. Add the following entry (use the absolute path to your `build/index.js`):

```json
{
  "mcpServers": {
    "cdli": {
      "command": "node",
      "args": ["/PATH/TO/CLONED/REPO/cdli-mcp-server/build/index.js"]
    }
  }
}
```

4. Restart Claude Desktop. You will now see the CDLI tools available in your conversation.

---

## Available Tools

### `get_artifact`
Fetches the full metadata record for a specific CDLI artifact by its ID.

The response includes publications, materials, period, provenience, collections, and the **full ATF inscription/transliteration text** (in the `inscription.atf` field). There is no need for a separate inscription tool — all transliteration data is embedded in this response.

| Parameter | Type   | Required | Description                      |
|-----------|--------|----------|----------------------------------|
| `id`      | string | ✅       | The CDLI artifact ID — accepts both prefixed (`P315278`) and numeric-only (`315278`) formats |

**Example prompt:** *"Get the full metadata and inscription text for artifact P315278"*

---

### `search_artifacts`
Performs a full-text search across the CDLI artifact catalog.

| Parameter | Type   | Required | Description              |
|-----------|--------|----------|--------------------------|
| `query`   | string | ✅       | The search term or phrase |

**Example prompt:** *"Search CDLI for tablets from the Ur III period"*

---

### `get_authors`
Returns a list of authors registered in the CDLI database (up to 20).

*No parameters required.*

**Example prompt:** *"List the authors in the CDLI database"*

---

### `get_publications`
Returns a list of publications from the CDLI database.

| Parameter | Type   | Required | Description                                 |
|-----------|--------|----------|---------------------------------------------|
| `limit`   | number | ❌       | Number of results to return (default: 20)   |

**Example prompt:** *"List publications from the CDLI database"*

---

### `get_provenience`
Returns a list of proveniences (archaeological find sites) registered in CDLI.

| Parameter | Type   | Required | Description                                 |
|-----------|--------|----------|---------------------------------------------|
| `limit`   | number | ❌       | Number of results to return (default: 20)   |

**Example prompt:** *"What proveniences are recorded in CDLI?"*

---


### `ping`
A simple liveness check to verify the server is running and reachable.

*No parameters required.*

**Example prompt:** *"Ping the CDLI server"*

---

## Development Notes

- All tools are defined in `src/tools/<tool-name>/index.ts` and must export `name`, `description`, `inputSchema`, and `handler`.
- To add a new tool: create a new folder under `src/tools/`, implement the exports, and register it in `src/tools/index.ts`.
- This server currently targets the live CDLI API at `https://cdli.mpiwg-berlin.mpg.de`.

---

## License

MIT
