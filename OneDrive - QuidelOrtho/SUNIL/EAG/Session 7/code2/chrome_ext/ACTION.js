// ACTION.js — Query processing, snippet scoring, and highlighting logic
// [arch] Coordinates search and result rendering, delegates to MEMORY for vectors
// [action] Opens URLs and triggers highlight in content script

const ACTION = {
  // [algo] Process search query
  async processQuery(query, k = 10) {
    console.log('[ACTION] Processing query:', query);
    
    // [decision] Validate query
    if (!query || query.trim().length < 2) {
      return {
        success: false,
        error: 'Query too short. Please enter at least 2 characters.'
      };
    }

    // [memory] Ensure bundle is loaded
    if (!MEMORY.isLoaded) {
      const loadResult = await MEMORY.loadBundle();
      if (!loadResult.success) {
        return {
          success: false,
          error: 'Failed to load search index. Please import your bundle.',
          needsBundle: true
        };
      }
    }

    // [algo] Search using hybrid approach
    const results = MEMORY.hybridSearch(query, k);
    
    if (results.length === 0) {
      return {
        success: true,
        results: [],
        message: 'No results found. Try different keywords or capture more pages.'
      };
    }

    // [algo] Format results for display
    const formatted = results.map(r => ({
      id: r.id,
      url: r.url,
      title: r.title,
      snippet: this.extractSnippet(r.chunk_text, query),
      score: r.score,
      fullText: r.chunk_text
    }));

    return {
      success: true,
      results: formatted,
      count: formatted.length
    };
  },

  // [algo] Extract snippet around query terms
  extractSnippet(text, query, contextChars = 150) {
    if (!text) return '';
    
    // [algo] Find position of first query word
    const queryWords = query.toLowerCase().split(/\s+/);
    const textLower = text.toLowerCase();
    
    let bestPos = -1;
    for (const word of queryWords) {
      const pos = textLower.indexOf(word);
      if (pos !== -1) {
        bestPos = pos;
        break;
      }
    }
    
    if (bestPos === -1) {
      // [fallback] No match found, return start
      return text.substring(0, contextChars * 2) + '...';
    }
    
    // [algo] Extract context window
    const start = Math.max(0, bestPos - contextChars);
    const end = Math.min(text.length, bestPos + contextChars);
    
    let snippet = text.substring(start, end);
    
    // [ux] Add ellipsis
    if (start > 0) snippet = '...' + snippet;
    if (end < text.length) snippet = snippet + '...';
    
    return snippet;
  },

  // [action] Open result URL and highlight snippet
  async openAndHighlight(url, snippet) {
    console.log('[ACTION] Opening and highlighting:', url);
    
    try {
      // [io] Open or focus tab with the URL
      // [action] Append #ragq= anchor for content script to detect
      const targetUrl = `${url}#ragq=${encodeURIComponent(snippet)}`;
      
      // [io] Create or update tab
      const tab = await chrome.tabs.create({ url: targetUrl });
      
      // [action] Wait for tab to load, then send highlight message
      // Note: The content script will also auto-detect #ragq= on load
      setTimeout(async () => {
        try {
          await chrome.tabs.sendMessage(tab.id, {
            type: 'HIGHLIGHT_SNIPPET',
            snippet: snippet
          });
        } catch (error) {
          // Content script will handle it via hash detection
          console.log('[ACTION] Content script will handle via hash');
        }
      }, 2000);
      
      return { success: true };
    } catch (error) {
      console.error('[ACTION] Error opening URL:', error);
      return { success: false, error: error.message };
    }
  },

  // [algo] Score snippet relevance (for re-ranking)
  scoreSnippet(snippet, query) {
    const snippetLower = snippet.toLowerCase();
    const queryWords = query.toLowerCase().split(/\s+/);
    
    let score = 0;
    for (const word of queryWords) {
      if (snippetLower.includes(word)) {
        score += 1;
      }
    }
    
    return score / queryWords.length;
  }
};

// Export for use in popup
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ACTION;
}

