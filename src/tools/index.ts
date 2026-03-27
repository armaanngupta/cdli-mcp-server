import * as getArtifact from './get-artifact/index.js';
import * as getAuthors from './get-authors/index.js';
import * as advancedSearch from './advanced-search/index.js';
import * as ping from './ping/index.js';
import * as getPublications from './get-publications/index.js';
import * as getProvenience from './get-provenience/index.js';
import * as getTranslation from './get-translation/index.js';

export const tools = [
    getArtifact,
    getAuthors,
    advancedSearch,
    ping,
    getPublications,
    getProvenience,
    getTranslation,
];
