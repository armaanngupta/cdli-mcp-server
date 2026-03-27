export const name = "get_cdli_metadata";
export const description = "Fetches standard JSON metadata for CDLI catalog entities. Use this to get details about artifacts, publications, historical periods, rulers, authors, and archives.";
export const inputSchema = {
    type: "object",
    properties: {
        resource: {
            type: "string",
            description: "The category to fetch. Supported paths include: artifacts, publications, authors, rulers, dynasties, periods, archives, collections, genres, materials, proveniences."
        },
        id: {
            type: "string",
            description: "The specific ID of the resource. If omitted, returns a paginated list of resources."
        },
        limit: {
            type: "number",
            description: "Number of resources to return if id is omitted (default: 20)."
        },
        page: {
            type: "number",
            description: "Page number for pagination (default: 1)."
        }
    },
    required: ["resource"]
};

export const handler = async (args: { resource: string, id?: string, limit?: number, page?: number }) => {
    const baseUrl = process.env.CDLI_API_BASE_URL || "https://cdli.earth";
    
    try {
        let url = `${baseUrl}/${args.resource}`;
        if (args.id) {
            url += `/${args.id}`;
        } else {
            const limit = args.limit ?? 20;
            const page = args.page ?? 1;
            url += `?limit=${limit}&page=${page}`;
        }

        const response = await fetch(url, {
            headers: { 
                'Accept': 'application/json',
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
            return { content: [{ type: "text", text: `API error fetching metadata: ${response.statusText}` }], isError: true };
        }
        const data = await response.json();
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    } catch (e: any) {
        return { content: [{ type: "text", text: `Error fetching metadata: ${e.message}` }], isError: true };
    }
};
