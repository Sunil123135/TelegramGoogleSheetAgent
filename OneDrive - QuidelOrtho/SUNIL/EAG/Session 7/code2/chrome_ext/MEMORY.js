// MEMORY.js — Bundle loader and cosine search engine
// [arch] Loads vectors.bin + meta.json, performs in-browser cosine similarity search
// [perf] All operations are local, no network calls

const MEMORY = {
  // [state] Loaded data
  vectors: null,
  meta: null,
  dim: 768, // Default embedding dimension
  
  // [state] Is bundle loaded?
  isLoaded: false,

  // [io] Load bundle from extension directory
  async loadBundle() {
    try {
      console.log('[MEMORY] Loading bundle...');
      
      // [io] Load vectors.bin
      const vectorsUrl = chrome.runtime.getURL('bundle/vectors.bin');
      const vectorsResponse = await fetch(vectorsUrl);
      const vectorsBuffer = await vectorsResponse.arrayBuffer();
      
      // [io] Load meta.json
      const metaUrl = chrome.runtime.getURL('bundle/meta.json');
      const metaResponse = await fetch(metaUrl);
      this.meta = await metaResponse.json();
      
      // [algo] Parse float32 vectors
      const float32Array = new Float32Array(vectorsBuffer);
      const numVectors = this.meta.length;
      this.dim = float32Array.length / numVectors;
      
      // [error] Dimension check
      if (!Number.isInteger(this.dim)) {
        throw new Error(`Dimension mismatch: ${float32Array.length} floats, ${numVectors} vectors`);
      }
      
      console.log(`[MEMORY] Loaded ${numVectors} vectors, dim=${this.dim}`);
      
      // [perf] Store as typed array for fast access
      this.vectors = float32Array;
      this.isLoaded = true;
      
      return { success: true, count: numVectors, dim: this.dim };
    } catch (error) {
      console.error('[MEMORY] Failed to load bundle:', error);
      this.isLoaded = false;
      return { success: false, error: error.message };
    }
  },

  // [algo] Normalize vector (L2 norm)
  normalize(vec) {
    let norm = 0;
    for (let i = 0; i < vec.length; i++) {
      norm += vec[i] * vec[i];
    }
    norm = Math.sqrt(norm);
    
    if (norm < 1e-12) return vec;
    
    const normalized = new Float32Array(vec.length);
    for (let i = 0; i < vec.length; i++) {
      normalized[i] = vec[i] / norm;
    }
    return normalized;
  },

  // [algo] Compute cosine similarity (assumes normalized vectors)
  cosineSimilarity(a, b) {
    let dot = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
    }
    return dot;
  },

  // [algo] Simple embedding stub (character bag-of-words)
  // [note] This is a placeholder. In production, swap with transformers.js or ONNX Runtime
  embedQuery(query) {
    const vec = new Float32Array(this.dim).fill(0);
    
    // [algo] Character n-gram hashing into dimension space
    const text = query.toLowerCase();
    for (let i = 0; i < text.length - 1; i++) {
      const bigram = text.charCodeAt(i) * 256 + text.charCodeAt(i + 1);
      const idx = bigram % this.dim;
      vec[idx] += 1;
    }
    
    return this.normalize(vec);
  },

  // [algo] Search top-k most similar vectors
  search(queryVec, k = 10) {
    if (!this.isLoaded) {
      console.error('[MEMORY] Bundle not loaded');
      return [];
    }

    console.log('[MEMORY] Searching...');
    const numVectors = this.meta.length;
    const scores = new Array(numVectors);
    
    // [perf] Compute cosine similarity for all vectors
    for (let i = 0; i < numVectors; i++) {
      const start = i * this.dim;
      const vecSlice = this.vectors.slice(start, start + this.dim);
      scores[i] = {
        id: i,
        score: this.cosineSimilarity(queryVec, vecSlice)
      };
    }
    
    // [algo] Sort by score descending
    scores.sort((a, b) => b.score - a.score);
    
    // [algo] Return top-k with metadata
    return scores.slice(0, k).map(s => ({
      ...this.meta[s.id],
      score: s.score
    }));
  },

  // [algo] Lexical fallback search (simple keyword overlap)
  lexicalSearch(query, k = 10) {
    if (!this.isLoaded) {
      console.error('[MEMORY] Bundle not loaded');
      return [];
    }

    console.log('[MEMORY] Lexical fallback search...');
    const queryWords = query.toLowerCase().split(/\s+/);
    const scores = [];
    
    for (let i = 0; i < this.meta.length; i++) {
      const text = (this.meta[i].chunk_text || '').toLowerCase();
      let score = 0;
      
      for (const word of queryWords) {
        if (text.includes(word)) {
          score += 1;
        }
      }
      
      if (score > 0) {
        scores.push({
          ...this.meta[i],
          score: score / queryWords.length
        });
      }
    }
    
    scores.sort((a, b) => b.score - a.score);
    return scores.slice(0, k);
  },

  // [decision] Hybrid search: semantic + lexical blend
  hybridSearch(query, k = 10) {
    if (!this.isLoaded) {
      return [];
    }

    // [algo] Get semantic results
    const queryVec = this.embedQuery(query);
    const semanticResults = this.search(queryVec, k * 2);
    
    // [algo] If semantic results are weak, blend with lexical
    if (semanticResults.length === 0 || semanticResults[0].score < 0.3) {
      console.log('[MEMORY] Weak semantic results, adding lexical...');
      const lexicalResults = this.lexicalSearch(query, k);
      
      // [algo] Merge and deduplicate
      const merged = [...semanticResults];
      const ids = new Set(semanticResults.map(r => r.id));
      
      for (const r of lexicalResults) {
        if (!ids.has(r.id)) {
          merged.push(r);
        }
      }
      
      return merged.slice(0, k);
    }
    
    return semanticResults.slice(0, k);
  }
};

// Export for use in popup and background
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MEMORY;
}

