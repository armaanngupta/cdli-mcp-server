export const name = "get_authors";

export const description = "Get a list of CDLI authors";

export const inputSchema = {
    type: "object",
    properties: {
        limit: {
            type: "number",
            description: "Number of authors to return (default: 20)"
        },
        offset: {
            type: "number",
            description: "Number of authors to skip for pagination (default: 0)"
        }
    }
};

export const handler = async (args: { limit?: number, offset?: number }) => {
    const limit = args.limit ?? 20;
    const offset = args.offset ?? 0;
    try {
        const response = await fetch(`https://cdli.earth/authors.json?limit=${limit}&offset=${offset}`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'cdli-mcp-prototype/1.0.0' }
        });
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `API error fetching authors.` }],
                isError: true,
            };
        }
        const authors = await response.json();
        return {
            content: [{ type: "text", text: JSON.stringify(authors, null, 2) }]
        };
    } catch (e: any) {
        return {
            content: [{ type: "text", text: `Error fetching authors: ${e.message}` }],
            isError: true,
        };
    }
};
