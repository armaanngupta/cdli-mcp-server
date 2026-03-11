export const name = "get_provenience";

export const description =
    "Get a list of proveniences (archaeological find sites) from the CDLI database. Optionally limit results.";

export const inputSchema = {
    type: "object",
    properties: {
        limit: {
            type: "number",
            description: "Number of proveniences to return (default: 20)"
        }
    },
    required: []
};

export const handler = async (args: { limit?: number }) => {
    const limit = args.limit ?? 20;
    try {
        const response = await fetch(
            `https://cdli.earth/proveniences.json?limit=${limit}`,
            { headers: { Accept: "application/json", "User-Agent": "cdli-mcp-server/1.0.0" } }
        );
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `API error fetching proveniences (status ${response.status}).` }],
                isError: true
            };
        }
        const data = await response.json();
        return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
        };
    } catch (e: any) {
        return {
            content: [{ type: "text", text: `Error fetching proveniences: ${e.message}` }],
            isError: true
        };
    }
};
