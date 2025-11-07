// DECISION.js — Policies for skip list, capture size, debounce, and fallbacks
// [arch] Central policy module shared by PERCEPTION and AGENT
// [security] Skip confidential domains to protect user privacy

const DECISION = {
  // [security] Domains to skip — no capture on sensitive sites
  SKIP_DOMAINS: [
    'gmail.com',
    'mail.google.com',
    'whatsapp.com',
    'web.whatsapp.com',
    'accounts.google.com',
    'login.live.com',
    'facebook.com/messages',
    'messenger.com',
    'mail.yahoo.com',
    'outlook.live.com',
    'outlook.office.com',
    // Banking keywords
    'netbanking',
    'ebanking',
    'onlinebanking',
    'secure.login',
    'auth.',
    'signin',
    'login',
  ],

  // [security] Skip keywords in URL
  SKIP_KEYWORDS: [
    'bank',
    'payment',
    'checkout',
    'wallet',
    'paypal',
    'stripe',
    'auth',
    'oauth',
    'saml',
    'sso'
  ],

  // [perf] Maximum text length to capture per page
  MAX_TEXT_LENGTH: 8000,

  // [perf] Debounce delay in ms before capturing (avoid rapid navigation)
  DEBOUNCE_DELAY: 2000,

  // [perf] Minimum text length to consider valid
  MIN_TEXT_LENGTH: 100,

  // [algo] Chunk size for embedding (used in Colab, documented here)
  CHUNK_SIZE: 800,
  CHUNK_OVERLAP: 120,

  // [decision] Should we skip this URL?
  shouldSkipUrl(url) {
    if (!url || !url.startsWith('http')) return true;
    
    const lowerUrl = url.toLowerCase();
    
    // Check skip domains
    for (const domain of this.SKIP_DOMAINS) {
      if (lowerUrl.includes(domain.toLowerCase())) {
        console.log(`[DECISION] Skipping domain: ${domain}`);
        return true;
      }
    }
    
    // Check skip keywords
    for (const keyword of this.SKIP_KEYWORDS) {
      if (lowerUrl.includes(keyword.toLowerCase())) {
        console.log(`[DECISION] Skipping keyword: ${keyword}`);
        return true;
      }
    }
    
    return false;
  },

  // [algo] Clean and normalize text for storage
  cleanText(text) {
    if (!text) return '';
    
    // Remove excessive whitespace
    text = text.replace(/\s+/g, ' ').trim();
    
    // Limit length
    if (text.length > this.MAX_TEXT_LENGTH) {
      text = text.substring(0, this.MAX_TEXT_LENGTH);
    }
    
    return text;
  },

  // [decision] Is this text valid for capture?
  isValidText(text) {
    return text && text.length >= this.MIN_TEXT_LENGTH;
  },

  // [error] Get fallback message for missing bundle
  getMissingBundleMessage() {
    return {
      type: 'error',
      message: 'Index bundle not found. Please build and import your bundle.',
      action: 'import_bundle'
    };
  },

  // [error] Get fallback for zero results
  getNoResultsMessage(query) {
    return {
      type: 'warning',
      message: `No results found for "${query}". Try capturing more pages or rebuilding your index.`,
      action: 'export_pages'
    };
  }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DECISION;
}

