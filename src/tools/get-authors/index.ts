export const name = "get_authors";

export const description = "Get a list of CDLI authors";

export const inputSchema = {
    type: "object",
    properties: {}
};

export const handler = async (args: any) => {
    try {
        const response = await fetch('https://cdli.earth/authors.json?limit=20', {
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
