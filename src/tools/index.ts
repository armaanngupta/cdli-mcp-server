import * as getArtifact from './get-artifact/index.js';
import * as getAuthors from './get-authors/index.js';
import * as searchArtifacts from './search-artifacts/index.js';
import * as ping from './ping/index.js';

export const tools = [
    getArtifact,
    getAuthors,
    searchArtifacts,
    ping
];
