import * as advancedSearch from './advanced-search/index.js';
import * as ping from './ping/index.js';
import * as groundTerm from './ground-term/index.js';
import * as getCdliMetadata from './get-cdli-metadata/index.js';
import * as getCdliLinkedData from './get-cdli-linked-data/index.js';
import * as getCdliBibliography from './get-cdli-bibliography/index.js';
import * as getCdliInscription from './get-cdli-inscription/index.js';
import * as searchEntity from './search-entity/index.js';

export const tools = [
    advancedSearch,
    ping,
    groundTerm,
    getCdliMetadata,
    getCdliLinkedData,
    getCdliBibliography,
    getCdliInscription,
    searchEntity,
];
