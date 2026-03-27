import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const name = "ground_term";

export const description = "Normalises a user-provided term to the closest CDLI canonical value.";

export const inputSchema = {
  type: "object",
  properties: {
    field: { 
      type: "string", 
      description: "One of: provenience, period, collection, genre, language" 
    },
    value: { 
      type: "string", 
      description: "User-provided term (may contain typos)" 
    }
  },
  required: ["field", "value"]
};

// Simple Levenshtein distance
function levenshtein(a: string, b: string): number {
  const matrix = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;

  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      if (a[i - 1] === b[j - 1]) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,    // deletion
          matrix[i][j - 1] + 1,    // insertion
          matrix[i - 1][j - 1] + 1 // substitution
        );
      }
    }
  }
  return matrix[a.length][b.length];
}

export const handler = async (args: any) => {
  const { field, value } = args;
  
  try {
    const termsPath = path.join(__dirname, 'terms.json');
    const termsData = JSON.parse(fs.readFileSync(termsPath, 'utf8'));
    
    const dict = termsData[field];
    if (!dict) {
      return { content: [{ type: "text", text: `No grounding data for field ${field}` }], isError: true };
    }

    const dictArray = Array.isArray(dict) ? dict : [];

    const best = dictArray.reduce(
      (bestOpt: { candidate: string; dist: number }, candidate: string) => {
        const dist = levenshtein(String(value).toLowerCase(), candidate.toLowerCase());
        return dist < bestOpt.dist ? { candidate, dist } : bestOpt;
      },
      { candidate: "", dist: Infinity }
    );

    if (best.dist <= 2) {
      return { content: [{ type: "text", text: best.candidate }] };
    }

    // No confident match – return the original value (LLM can decide)
    return { content: [{ type: "text", text: String(value) }] };
  } catch (err: any) {
    return { content: [{ type: "text", text: `Error reading grounding data: ${err.message}` }], isError: true };
  }
};
