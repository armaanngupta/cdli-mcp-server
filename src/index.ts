import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { tools } from "./tools/index.js";

// 1. Initialize Server
const server = new Server(
    {
        name: "cdli-mcp-prototype",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// 2. Expose Tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: tools.map((tool) => ({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema,
        })),
    };
});

// 3. Handle Tool Execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const toolName = request.params.name;
    const args = request.params.arguments || {};

    const tool = tools.find((t) => t.name === toolName);
    if (!tool) {
        throw new Error(`Unknown tool: ${toolName}`);
    }

    return await tool.handler(args as any);
});

// 4. Connect Transport
async function run() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    // Intentionally removed console.error since it can break some strict Stdio RPC clients
}

run().catch((error) => {
    // We can write to stderr for fatals, but generally we avoid logging when testing inside stdio
    process.stderr.write(`Fatal error running MCP server: ${error.message}\n`);
    process.exit(1);
});
