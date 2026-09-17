// Lightweight replacement for the Python sklearn TF-IDF + cosine-similarity
// retrieval used in the original Streamlit app. No native deps required.

export function chunkText(text: string, chunkSize = 400, overlap = 50): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const chunks: string[] = [];
  const step = Math.max(1, chunkSize - overlap);
  for (let i = 0; i < words.length; i += step) {
    const chunk = words.slice(i, i + chunkSize).join(" ").trim();
    if (chunk) chunks.push(chunk);
  }
  return chunks;
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}

function termFreq(tokens: string[]): Map<string, number> {
  const tf = new Map<string, number>();
  for (const t of tokens) tf.set(t, (tf.get(t) ?? 0) + 1);
  return tf;
}

function cosineSimilarity(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  for (const [term, count] of a) {
    const other = b.get(term);
    if (other) dot += count * other;
  }
  const normA = Math.sqrt([...a.values()].reduce((s, v) => s + v * v, 0));
  const normB = Math.sqrt([...b.values()].reduce((s, v) => s + v * v, 0));
  if (normA === 0 || normB === 0) return 0;
  return dot / (normA * normB);
}

export function retrieveRelevantChunks(query: string, chunks: string[], topK = 6): string {
  if (!chunks || chunks.length === 0) return "";

  const queryVec = termFreq(tokenize(query));
  const scored = chunks.map((chunk, idx) => ({
    idx,
    chunk,
    score: cosineSimilarity(queryVec, termFreq(tokenize(chunk))),
  }));

  scored.sort((a, b) => b.score - a.score);
  const top = scored.slice(0, topK).filter((s) => s.score > 0);

  if (top.length === 0) {
    // fall back to the first few chunks, same as the Python version's except branch
    return chunks.slice(0, topK).join("\n\n---\n\n");
  }
  return top.map((s) => s.chunk).join("\n\n---\n\n");
}
