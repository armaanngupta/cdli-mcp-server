export const name = "get_artifact";

export const description = "Get metadata for a specific CDLI artifact by ID";

export const inputSchema = {
    type: "object",
    properties: {
        id: { type: "string", description: "The ID of the artifact (e.g. 1, 2, 3)" }
    },
    required: ["id"]
};

export const handler = async (args: any) => {
    const id = args.id as string;
    try {
        const response = await fetch(`https://cdli.mpiwg-berlin.mpg.de/artifacts/${id}.json`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'cdli-mcp-prototype/1.0.0' }
        });
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `Artifact ${id} not found or API error.` }],
                isError: true,
            };
        }
        const artifact = await response.json();
        return {
            content: [{ type: "text", text: JSON.stringify(artifact, null, 2) }]
        };
    } catch (e: any) {
        return {
            content: [{ type: "text", text: `Error fetching artifact: ${e.message}` }],
            isError: true,
        };
    }
};
