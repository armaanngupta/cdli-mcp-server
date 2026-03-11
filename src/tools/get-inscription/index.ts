export const name = "get_inscription";

export const description =
    "Get the inscription (transliteration text) for a specific CDLI artifact by its ID.";

export const inputSchema = {
    type: "object",
    properties: {
        id: {
            type: "string",
            description: "The CDLI artifact ID (e.g. P315278)"
        }
    },
    required: ["id"]
};

export const handler = async (args: { id: string }) => {
    const id = args.id;
    try {
        const response = await fetch(
            `https://cdli.mpiwg-berlin.mpg.de/artifacts/${id}/inscription`,
            { headers: { Accept: "application/json", "User-Agent": "cdli-mcp-server/1.0.0" } }
        );
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `Inscription for artifact ${id} not found or API error (status ${response.status}).` }],
                isError: true
            };
        }
        const data = await response.json();
        return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
        };
    } catch (e: any) {
        return {
            content: [{ type: "text", text: `Error fetching inscription: ${e.message}` }],
            isError: true
        };
    }
};
