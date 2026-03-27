export const name = "get_translation";

export const description =
    "Get the inscription (transliteration text) for a specific CDLI artifact by its ID.";

export const inputSchema = {
    type: "object",
    properties: {
        id: {
            type: "string",
            description: "The CDLI artifact ID — accepts both prefixed (e.g. P315278) and numeric-only (e.g. 315278) formats"
        }
    },
    required: ["id"]
};

export const handler = async (args: { id: string }) => {
    // Normalize: strip leading letter prefix (e.g. "P315278" -> "315278")
    const numericId = args.id.replace(/^[A-Za-z]+/, "");
    try {
        const response = await fetch(
            `https://cdli.earth/artifacts/${numericId}/inscription`,
            { headers: { Accept: "application/json", "User-Agent": "cdli-mcp-server/1.0.0" } }
        );
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `Inscription for artifact ${numericId} not found or API error (status ${response.status}).` }],
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
