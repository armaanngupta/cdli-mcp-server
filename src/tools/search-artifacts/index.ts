export const name = "search_artifacts";

export const description = "Search for artifacts by full-text query";

export const inputSchema = {
    type: "object",
    properties: {
        query: { type: "string", description: "Search term" }
    },
    required: ["query"]
};

export const handler = async (args: any) => {
    const query = args.query as string;
    try {
        const response = await fetch(`https://cdli.earth/search.json?query=${encodeURIComponent(query)}&limit=10`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'cdli-mcp-prototype/1.0.0' }
        });
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `API error searching artifacts.` }],
                isError: true,
            };
        }
        const results = await response.json();
        return {
            content: [{ type: "text", text: JSON.stringify(results, null, 2) }]
        };
    } catch (e: any) {
        return {
            content: [{ type: "text", text: `Error searching artifacts: ${e.message}` }],
            isError: true,
        };
    }
};
