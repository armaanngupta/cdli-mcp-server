export const name = "get_artifact";

export const description = "Get full metadata for a specific CDLI artifact by ID, including its publications, materials, period, provenience, collections, and the full ATF inscription/transliteration text (in the `inscription.atf` field).";

export const inputSchema = {
    type: "object",
    properties: {
        id: { type: "string", description: "The ID of the artifact (e.g. 1, 2, 3)" }
    },
    required: ["id"]
};

export const handler = async (args: { id: string }) => {
    // Normalize: strip leading letter prefix (e.g. "P234524" -> "234524")
    const numericId = args.id.replace(/^[A-Za-z]+/, "");
    try {
        const response = await fetch(`https://cdli.mpiwg-berlin.mpg.de/artifacts/${numericId}.json`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'cdli-mcp-prototype/1.0.0' }
        });
        if (!response.ok) {
            return {
                content: [{ type: "text", text: `Artifact ${numericId} not found or API error.` }],
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
