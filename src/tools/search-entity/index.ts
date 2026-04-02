export const name = "search_entity";
export const description = "Search across multiple CDLI non-artifact entities (authors, proveniences, languages, collections, materials, regions, periods, genres). This tool maps unified filters to CDLI parameters and normalizes the output.";

export const inputSchema = {
    type: "object",
    properties: {
        entity_type: {
            type: "string",
            enum: ["authors", "proveniences", "languages", "collections", "materials", "regions", "periods", "genres"],
            description: "The type of entity to search for."
        },
        filters: {
            type: "object",
            additionalProperties: { type: "string" },
            description: "A key-value map of filters. Use 'name' for general text search. E.g., {'name': 'alexander'}. Other specific keys: 'orcid' (authors), 'region' (proveniences), 'parent' (languages)."
        },
        limit: {
            type: "number",
            description: "Number of results to return (default: 20)."
        },
        page: {
            type: "number",
            description: "Page number for pagination (default: 1)."
        }
    },
    required: ["entity_type", "filters"]
};

const FIELD_MAP: Record<string, Record<string, string>> = {
    authors: { name: "author", orcid: "orcid" },
    proveniences: { name: "provenience", region: "region" },
    languages: { name: "language", parent: "parent" },
    collections: { name: "collection" },
    materials: { name: "material" },
    regions: { name: "region" },
    periods: { name: "period" },
    genres: { name: "genre" }
};

export const handler = async (args: { entity_type: string, filters: Record<string, string>, limit?: number, page?: number }) => {
    const { entity_type, filters } = args;
    
    // 1. Validate entity_type
    const map = FIELD_MAP[entity_type];
    if (!map) {
        return { content: [{ type: "text", text: `Unknown entity_type: ${entity_type}. Supported types: ${Object.keys(FIELD_MAP).join(", ")}` }], isError: true };
    }

    if (!filters || Object.keys(filters).length === 0) {
        return { content: [{ type: "text", text: "Filters object cannot be empty." }], isError: true };
    }

    const limit = args.limit ?? 20;
    const page = args.page ?? 1;

    // 2. Map filters to URL params
    const params = new URLSearchParams();
    params.set("limit", limit.toString());
    params.set("page", page.toString());

    for (const [filterKey, filterValue] of Object.entries(filters)) {
        const cdliParam = map[filterKey];
        if (cdliParam) {
            params.set(cdliParam, filterValue);
        }
    }

    // 3. Construct URL
    const baseUrl = process.env.CDLI_API_BASE_URL || "https://cdli.earth";
    const url = `${baseUrl}/${entity_type}?${params.toString()}`;

    // 5. Make request
    try {
        const response = await fetch(url, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'cdli-mcp-server/1.0.0' }
        });

        if (!response.ok) {
            return { content: [{ type: "text", text: `API error searching ${entity_type}: HTTP ${response.status} - ${response.statusText}` }], isError: true };
        }

        const data = await response.json();
        const entities: any[] = Array.isArray(data) ? data : (Array.isArray(data.entities) ? data.entities : []);

        if (entities.length === 0) {
            return { content: [{ type: "text", text: JSON.stringify({ results: [], total: data.paging?.count || 0 }, null, 2) }] };
        }

        // 7. Normalize response
        const normalizedResults = entities.map((entity: any) => {
            const id = entity.id || entity.author_id || entity.provenience_id || entity.language_id || entity.collection_id || entity.material_id || entity.region_id || entity.period_id || entity.genre_id || Object.values(entity)[0];
            const name = entity.name || entity.author || entity.provenience || entity.language || entity.collection || entity.material || entity.region || entity.period || entity.genre || entity.title || "Unknown";

            return {
                id: String(id),
                name: String(name),
                raw: entity
            };
        });

        const output = {
            results: normalizedResults,
            total: data.paging?.count || normalizedResults.length
        };

        return { content: [{ type: "text", text: JSON.stringify(output, null, 2) }] };
    } catch (e: any) {
        return { content: [{ type: "text", text: `Network error searching ${entity_type}: ${e.message}` }], isError: true };
    }
};
