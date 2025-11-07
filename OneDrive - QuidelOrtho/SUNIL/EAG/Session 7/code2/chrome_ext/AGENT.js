// AGENT.js — Service Worker (Background) orchestration
// [arch] Manages messaging, storage, export/import, tab management
// [agent] Coordinates all layers: PERCEPTION → MEMORY → ACTION

// Import other modules (MV3 service workers support ES modules)
// For now, we'll use inline logic since imports need proper setup

// [state] Storage keys
const STORAGE_KEYS = {
  PAGES: 'captured_pages',
  BUNDLE_META: 'bundle_metadata'
};

// [io] Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[AGENT] Received message:', message.type);
  
  // [async] Handle async responses
  handleMessage(message, sender).then(sendResponse);
  return true; // Keep channel open for async response
});

// [agent] Route messages to appropriate handlers
async function handleMessage(message, sender) {
  try {
    switch (message.type) {
      case 'CAPTURE_PAGE':
        return await handleCapturePage(message.data);
      
      case 'EXPORT_PAGES':
        return await handleExportPages();
      
      case 'GET_STATS':
        return await handleGetStats();
      
      case 'CLEAR_PAGES':
        return await handleClearPages();
      
      case 'SEARCH_QUERY':
        return await handleSearchQuery(message.query, message.k);
      
      default:
        return { success: false, error: 'Unknown message type' };
    }
  } catch (error) {
    console.error('[AGENT] Error handling message:', error);
    return { success: false, error: error.message };
  }
}

// [io] Handle page capture from content script
async function handleCapturePage(pageData) {
  try {
    // [io] Get existing pages
    const result = await chrome.storage.local.get(STORAGE_KEYS.PAGES);
    const pages = result[STORAGE_KEYS.PAGES] || [];
    
    // [decision] Check if page already captured (by URL)
    const existingIndex = pages.findIndex(p => p.url === pageData.url);
    
    if (existingIndex !== -1) {
      // [decision] Update existing entry
      pages[existingIndex] = pageData;
      console.log('[AGENT] Updated existing page:', pageData.url);
    } else {
      // [io] Add new page
      pages.push(pageData);
      console.log('[AGENT] Captured new page:', pageData.url);
    }
    
    // [io] Save back to storage
    await chrome.storage.local.set({ [STORAGE_KEYS.PAGES]: pages });
    
    return { success: true, totalPages: pages.length };
  } catch (error) {
    console.error('[AGENT] Error capturing page:', error);
    return { success: false, error: error.message };
  }
}

// [io] Export all captured pages as JSON
async function handleExportPages() {
  try {
    const result = await chrome.storage.local.get(STORAGE_KEYS.PAGES);
    const pages = result[STORAGE_KEYS.PAGES] || [];
    
    // [io] Create downloadable data URL (service worker compatible)
    const jsonData = JSON.stringify(pages, null, 2);
    const dataUrl = 'data:application/json;charset=utf-8,' + encodeURIComponent(jsonData);
    
    // [io] Trigger download
    await chrome.downloads.download({
      url: dataUrl,
      filename: `pages_${Date.now()}.json`,
      saveAs: true
    });
    
    console.log('[AGENT] Exported', pages.length, 'pages');
    return { success: true, count: pages.length };
  } catch (error) {
    console.error('[AGENT] Error exporting pages:', error);
    return { success: false, error: error.message };
  }
}

// [io] Get storage statistics
async function handleGetStats() {
  try {
    const result = await chrome.storage.local.get(STORAGE_KEYS.PAGES);
    const pages = result[STORAGE_KEYS.PAGES] || [];
    
    // [algo] Calculate stats
    const totalChars = pages.reduce((sum, p) => sum + (p.text?.length || 0), 0);
    const avgChars = pages.length > 0 ? Math.round(totalChars / pages.length) : 0;
    
    return {
      success: true,
      stats: {
        pageCount: pages.length,
        totalChars: totalChars,
        avgChars: avgChars,
        lastCaptured: pages.length > 0 ? pages[pages.length - 1].ts : null
      }
    };
  } catch (error) {
    console.error('[AGENT] Error getting stats:', error);
    return { success: false, error: error.message };
  }
}

// [io] Clear all captured pages
async function handleClearPages() {
  try {
    await chrome.storage.local.remove(STORAGE_KEYS.PAGES);
    console.log('[AGENT] Cleared all pages');
    return { success: true };
  } catch (error) {
    console.error('[AGENT] Error clearing pages:', error);
    return { success: false, error: error.message };
  }
}

// [agent] Handle search query (delegated from popup)
async function handleSearchQuery(query, k = 10) {
  // This is primarily handled in the popup with MEMORY.js
  // But we can log it here for monitoring
  console.log('[AGENT] Search query logged:', query);
  return { success: true, logged: true };
}

// [arch] Initialize service worker
console.log('[AGENT] Service worker initialized');

// [io] Handle installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('[AGENT] Extension installed/updated:', details.reason);
  
  if (details.reason === 'install') {
    // [ux] Open welcome page
    console.log('[AGENT] First install - welcome!');
  }
});

// [perf] Keep service worker alive with periodic tasks
// Note: MV3 service workers are event-driven and may sleep
setInterval(() => {
  console.log('[AGENT] Heartbeat');
}, 60000); // Every minute

