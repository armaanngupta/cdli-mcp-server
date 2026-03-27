import { handler as groundTerm } from '../ground-term/index.js';

export const name = "advanced_search";

export const description =
    "Search CDLI artifacts using specific fields. All parameters are optional — " +
    "combine any subset to filter results. Supports wildcards (* ?), boolean operators " +
    "(%AND% / %OR% within a field), quoted literals (\"exact phrase\"), and regex (/pattern/).";

export const inputSchema = {
    type: "object",
    properties: {
        // --- Object metadata ---
        designation: {
            type: "string",
            description: "Primary publication designation (e.g. 'MVN 3, 1'). Supports wildcards/regex.",
        },
        museum_no: {
            type: "string",
            description: "Museum number (e.g. 'BM 00001'). Tolerant of leading zero differences.",
        },
        accession_no: {
            type: "string",
            description: "Accession number.",
        },
        excavation_no: {
            type: "string",
            description: "Excavation number.",
        },
        cdli_id: {
            type: "string",
            description: "CDLI identifier (P-number, e.g. 'P254876'). Commas treated as OR.",
        },

        // --- Bibliographic ---
        publication_designation: {
            type: "string",
            description: "Publication designation (e.g. 'CUSAS 3, 1').",
        },
        publication_authors: {
            type: "string",
            description: "Publication author name(s). Use %AND% or %OR% for multiple authors.",
        },
        publication_editors: {
            type: "string",
            description: "Publication editor name(s).",
        },
        publication_year: {
            type: "string",
            description: "Publication year (e.g. '2003'). Supports range operators: >=2000, <2010.",
        },
        publication_title: {
            type: "string",
            description: "Title of the publication.",
        },
        publication_type: {
            type: "string",
            description: "Publication type (e.g. 'primary', 'history').",
        },
        publication_publisher: {
            type: "string",
            description: "Publisher name.",
        },
        publication_series: {
            type: "string",
            description: "Publication series name.",
        },

        // --- Artifact properties ---
        artifact_type: {
            type: "string",
            description: "Artifact type (e.g. 'tablet', 'cone', 'seal'). Use %OR% for multiple.",
        },
        material: {
            type: "string",
            description: "Material (e.g. 'clay', 'stone'). Use %OR% for multiple.",
        },
        period: {
            type: "string",
            description: "Historical period (e.g. 'Ur III'). Use %OR% for multiple periods.",
        },
        provenience: {
            type: "string",
            description: "Find-site / provenience (e.g. 'Lagash', 'Nippur'). Use %OR% for multiple.",
        },
        collection: {
            type: "string",
            description: "Holding museum/collection (e.g. 'British Museum').",
        },
        dates_referenced: {
            type: "string",
            description: "Dates referenced in the text (e.g. 'Šulgi 2').",
        },
        archive: {
            type: "string",
            description: "Archive name.",
        },
        genre: {
            type: "string",
            description: "Genre (e.g. 'Administrative', 'Literary'). Use %OR% for multiple.",
        },
        language: {
            type: "string",
            description: "Language of the text (e.g. 'Sumerian', 'Akkadian'). Use %OR% for multiple.",
        },

        // --- Textual / ATF ---
        atf_transliteration: {
            type: "string",
            description: "ATF transliteration text to search for within tablet inscriptions.",
        },
        atf_translation_text: {
            type: "string",
            description: "Search within English translations of inscriptions.",
        },
        atf_comments: {
            type: "string",
            description: "Search within ATF comments.",
        },

        // --- Composite / Seal ---
        composite_no: {
            type: "string",
            description: "Composite number (Q-number, e.g. 'Q000001').",
        },
        seal_no: {
            type: "string",
            description: "Seal number (S-number, e.g. 'S000001').",
        },
        all_composite_no: {
            type: "string",
            description: "Search across all composite numbers (composite and witness).",
        },
        all_seal_no: {
            type: "string",
            description: "Search across all seal numbers (seal and impression).",
        },

        // --- Update / contributor ---
        update_authors: {
            type: "string",
            description: "CDLI contributor / update author name.",
        },

        // --- Pagination ---
        limit: {
            type: "number",
            description: "Maximum number of results to return (default: 20, max: 100).",
        },
        offset: {
            type: "number",
            description: "Number of results to skip for pagination (default: 0).",
        },
    },
    required: [],
};

/** Fields that map directly 1:1 to an advanced search URL param. */
const FIELD_PARAMS: Record<string, string> = {
    designation:               "designation",
    museum_no:                 "museum_no",
    accession_no:              "accession_no",
    excavation_no:             "excavation_no",
    cdli_id:                   "cdli_id",
    publication_designation:   "publication_designation",
    publication_authors:       "publication_authors",
    publication_editors:       "publication_editors",
    publication_year:          "publication_year",
    publication_title:         "publication_title",
    publication_type:          "publication_type",
    publication_publisher:     "publication_publisher",
    publication_series:        "publication_series",
    artifact_type:             "artifact_type",
    material:                  "material",
    period:                    "period",
    provenience:               "provenience",
    collection:                "collection",
    dates_referenced:          "dates_referenced",
    archive:                   "archive",
    genre:                     "genre",
    language:                  "language",
    atf_transliteration:       "atf_transliteration",
    atf_translation_text:      "atf_translation_text",
    atf_comments:              "atf_comments",
    composite_no:              "composite_no",
    seal_no:                   "seal_no",
    all_composite_no:          "all_composite_no",
    all_seal_no:               "all_seal_no",
    update_authors:            "update_authors",
};

export const handler = async (args: Record<string, unknown>) => {
    const limit  = Math.min(Number(args.limit  ?? 20), 100);
    const offset = Number(args.offset ?? 0);

    const params = new URLSearchParams();
    params.set("limit",  String(limit));
    params.set("offset", String(offset));

    let hasFilter = false;
    for (const [argKey, paramKey] of Object.entries(FIELD_PARAMS)) {
        const value = args[argKey];
        if (value !== undefined && value !== null && value !== "") {
            const groundable = ["provenience", "period", "collection", "genre", "language"];
            if (groundable.includes(argKey)) {
                try {
                    const grounded = await groundTerm({ field: argKey, value: String(value) });
                    const corrected = grounded.content?.[0]?.text ?? String(value);
                    params.set(paramKey, corrected);
                } catch (e) {
                    params.set(paramKey, String(value));
                }
            } else {
                params.set(paramKey, String(value));
            }
            hasFilter = true;
        }
    }

    if (!hasFilter) {
        return {
            content: [{
                type: "text",
                text: "Please provide at least one search parameter (e.g. period, language, genre, museum_no).",
            }],
            isError: true,
        };
    }

    const url = `https://cdli.earth/search.json?${params.toString()}`;

    try {
        const response = await fetch(url, {
            headers: {
                "Accept":     "application/json",
                "User-Agent": "cdli-mcp-prototype/1.0.0",
            },
        });

        if (!response.ok) {
            return {
                content: [{
                    type: "text",
                    text: `CDLI API error: HTTP ${response.status} — ${response.statusText}`,
                }],
                isError: true,
            };
        }

        const results = await response.json() as any;

        // Build a human-readable citation list if the response contains entities
        const entities: any[] = Array.isArray(results?.entities)
            ? results.entities
            : Array.isArray(results)
                ? results
                : [];

        if (entities.length === 0) {
            return {
                content: [{
                    type: "text",
                    text: `No artifacts found for the given search parameters.\n\nQuery URL: ${url}`,
                }],
            };
        }

        const citations = entities.map((e: any) => {
            const id          = e.id ?? e.artifact_id ?? "?";
            const designation = e.designation ?? e.museum_no ?? "(no title)";
            return `P${String(id).padStart(6, "0")} — ${designation}\nhttps://cdli.earth/artifacts/${id}`;
        }).join("\n\n");

        const totalNote = results?.paging?.count !== undefined
            ? `\n\n(Showing ${entities.length} of ${results.paging.count} total results)`
            : "";

        return {
            content: [{
                type: "text",
                text: citations + totalNote,
            }],
        };

    } catch (e: any) {
        return {
            content: [{
                type: "text",
                text: `Network error calling CDLI API: ${e.message}\n\nQuery URL: ${url}`,
            }],
            isError: true,
        };
    }
};
