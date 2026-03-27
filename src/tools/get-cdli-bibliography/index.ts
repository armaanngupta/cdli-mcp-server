export const name = "get_cdli_bibliography";
export const description = "Retrieves bibliography export data for artifacts or publications.";
export const inputSchema = {
    type: "object",
    properties: {
        resource: {
            type: "string",
            enum: ["artifacts", "publications"],
            description: "The resource type to get citations for."
        },
        id: {
            type: "string",
            description: "The specific ID of the artifact or publication."
        },
        format: {
            type: "string",
            enum: ["BibTeX", "CSL-JSON"],
            description: "The requested bibliography format."
        }
    },
    required: ["resource", "id", "format"]
};

export const handler = async (args: { resource: string, id: string, format: string }) => {
    const baseUrl = process.env.CDLI_API_BASE_URL || "https://cdli.earth";
    
    let acceptHeader = 'application/json';
    if (args.format === 'BibTeX') {
        acceptHeader = 'application/x-bibtex';
    } else if (args.format === 'CSL-JSON') {
        acceptHeader = 'application/vnd.citationstyles.csl+json';
    }

    try {
        const response = await fetch(`${baseUrl}/${args.resource}/${args.id}`, {
            headers: { 
                'Accept': acceptHeader,
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
            return { content: [{ type: "text", text: `API error fetching bibliography: ${response.statusText}` }], isError: true };
        }
        
        const textData = await response.text();
        return { content: [{ type: "text", text: textData }] };
    } catch (e: any) {
        return { content: [{ type: "text", text: `Error fetching bibliography: ${e.message}` }], isError: true };
    }
};
