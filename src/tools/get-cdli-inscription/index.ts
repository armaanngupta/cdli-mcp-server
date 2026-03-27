export const name = "get_cdli_inscription";
export const description = "Fetches the physical text or transliteration of a specific inscription.";
export const inputSchema = {
    type: "object",
    properties: {
        id: {
            type: "string",
            description: "The ID of the inscription."
        },
        format: {
            type: "string",
            enum: ["C-ATF", "CDLI-CoNLL", "CoNLL-U"],
            description: "The format of the inscription text."
        }
    },
    required: ["id", "format"]
};

export const handler = async (args: { id: string, format: string }) => {
    const baseUrl = process.env.CDLI_API_BASE_URL || "https://cdli.earth";
    
    let acceptHeader = 'text/plain';
    if (args.format === 'C-ATF') {
        acceptHeader = 'text/x-c-atf';
    } else if (args.format === 'CDLI-CoNLL') {
        acceptHeader = 'text/x-cdli-conll';
    } else if (args.format === 'CoNLL-U') {
        acceptHeader = 'text/x-conll-u';
    }

    try {
        // Routing to /inscriptions/{id} as instructed for simplicity
        const response = await fetch(`${baseUrl}/inscriptions/${args.id}`, {
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
            return { content: [{ type: "text", text: `API error fetching inscription: ${response.statusText}` }], isError: true };
        }
        
        const textData = await response.text();
        return { content: [{ type: "text", text: textData }] };
    } catch (e: any) {
        return { content: [{ type: "text", text: `Error fetching inscription: ${e.message}` }], isError: true };
    }
};
