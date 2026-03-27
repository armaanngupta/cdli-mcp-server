export const name = "get_cdli_linked_data";
export const description = "Fetches Linked Open Data (JSON-LD) for CDLI catalog entities.";
export const inputSchema = {
    type: "object",
    properties: {
        resource: {
            type: "string",
            description: "The linked data category. Supported paths: archives, artifacts, collections, dates, dynasties, genres, inscriptions, languages, materials, periods, proveniences, publications, regions, rulers."
        },
        id: {
            type: "string",
            description: "The specific ID of the resource."
        }
    },
    required: ["resource", "id"]
};

export const handler = async (args: { resource: string, id: string }) => {
    const baseUrl = process.env.CDLI_API_BASE_URL || "https://cdli.earth";
    try {
        const response = await fetch(`${baseUrl}/${args.resource}/${args.id}`, {
            headers: { 
                'Accept': 'application/ld+json',
                'User-Agent': 'cdli-mcp-server/1.0.0'
            }
        });
        
        if (response.status === 404) {
            return { content: [{ type: "text", text: "Resource not found." }] };
        }
        if (response.status === 406) {
            return { content: [{ type: "text", text: "Format not supported for this resource." }] };
        }
        if (!response.ok) {
            return { content: [{ type: "text", text: `API error fetching linked data: ${response.statusText}` }], isError: true };
        }
        const data = await response.json();
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (e: any) {
        return { content: [{ type: "text", text: `Error fetching linked data: ${e.message}` }], isError: true };
    }
};
