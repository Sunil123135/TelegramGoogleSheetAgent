// PERCEPTION.js — Content script that captures page text
// [arch] Runs on every page, extracts clean text, respects DECISION policies
// [io] Sends captured data to AGENT via chrome.runtime.sendMessage

(function() {
  'use strict';
  
  // [perf] Debounce timer to avoid rapid captures
  let captureTimer = null;
  
  // [state] Track if we already captured this page
  let captured = false;

  // [algo] Extract clean text from page
  function extractPageText() {
    // [perf] Use textContent for simple extraction
    const bodyText = document.body?.textContent || '';
    return DECISION.cleanText(bodyText);
  }

  // [io] Capture current page and send to background
  function capturePage() {
    // [decision] Check if we should skip this URL
    if (DECISION.shouldSkipUrl(window.location.href)) {
      console.log('[PERCEPTION] Skipped capture (policy):', window.location.href);
      return;
    }

    // [algo] Extract and validate text
    const text = extractPageText();
    if (!DECISION.isValidText(text)) {
      console.log('[PERCEPTION] Skipped capture (text too short)');
      return;
    }

    // [io] Prepare page data
    const pageData = {
      url: window.location.href,
      title: document.title || 'Untitled',
      text: text,
      ts: Date.now()
    };

    // [io] Send to background service worker
    chrome.runtime.sendMessage({
      type: 'CAPTURE_PAGE',
      data: pageData
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('[PERCEPTION] Error sending page:', chrome.runtime.lastError);
        return;
      }
      captured = true;
      console.log('[PERCEPTION] Page captured:', pageData.url);
    });
  }

  // [perf] Debounced capture to avoid rapid-fire on dynamic pages
  function scheduledCapture() {
    if (captured) return; // Only capture once per page load
    
    if (captureTimer) {
      clearTimeout(captureTimer);
    }
    
    captureTimer = setTimeout(() => {
      capturePage();
    }, DECISION.DEBOUNCE_DELAY);
  }

  // [action] Check for highlight request (#ragq=...)
  function checkForHighlight() {
    const hash = window.location.hash;
    if (hash.startsWith('#ragq=')) {
      const query = decodeURIComponent(hash.substring(6));
      console.log('[PERCEPTION] Highlight request detected:', query);
      
      // Wait a bit for page to fully render
      setTimeout(() => {
        highlightSnippet(query);
      }, 500);
    }
  }

  // [action] Highlight best matching snippet on page
  function highlightSnippet(snippet) {
    try {
      // [algo] Get all text nodes
      const bodyText = document.body.textContent.toLowerCase();
      const snippetLower = snippet.toLowerCase();
      
      // [algo] Find best match position
      let matchIndex = bodyText.indexOf(snippetLower);
      
      if (matchIndex === -1) {
        // [algo] Try fuzzy match (first few words)
        const words = snippetLower.split(/\s+/).slice(0, 5).join(' ');
        matchIndex = bodyText.indexOf(words);
      }
      
      if (matchIndex === -1) {
        console.log('[PERCEPTION] Could not find snippet to highlight');
        return;
      }
      
      // [action] Find the actual DOM node containing the text
      const range = findTextRange(snippet.substring(0, 100));
      if (range) {
        // [action] Wrap in highlight element
        const mark = document.createElement('mark');
        mark.className = 'rag-highlight';
        mark.style.cssText = 'background-color: #ffeb3b; padding: 2px 0; border-radius: 2px; box-shadow: 0 0 10px rgba(255,235,59,0.5);';
        
        try {
          range.surroundContents(mark);
          // [ux] Scroll into view
          mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
          console.log('[PERCEPTION] Highlighted snippet');
        } catch (e) {
          // [error] Fallback: just scroll to approximate position
          console.warn('[PERCEPTION] Could not wrap text, using fallback scroll');
          window.scrollTo({
            top: document.body.scrollHeight * (matchIndex / bodyText.length),
            behavior: 'smooth'
          });
        }
      }
    } catch (error) {
      console.error('[PERCEPTION] Error highlighting:', error);
    }
  }

  // [algo] Find DOM range for text
  function findTextRange(searchText) {
    const searchLower = searchText.toLowerCase();
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let node;
    while (node = walker.nextNode()) {
      const text = node.textContent.toLowerCase();
      const index = text.indexOf(searchLower);
      
      if (index !== -1) {
        const range = document.createRange();
        range.setStart(node, index);
        range.setEnd(node, Math.min(index + searchText.length, node.length));
        return range;
      }
    }
    
    return null;
  }

  // [arch] Initialize on page load
  function init() {
    console.log('[PERCEPTION] Content script loaded');
    
    // [action] Check for highlight request
    checkForHighlight();
    
    // [io] Schedule page capture
    if (document.readyState === 'complete') {
      scheduledCapture();
    } else {
      window.addEventListener('load', scheduledCapture);
    }
    
    // [io] Listen for messages from popup/background
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.type === 'HIGHLIGHT_SNIPPET') {
        highlightSnippet(message.snippet);
        sendResponse({ success: true });
      }
      return true;
    });
  }

  // Start
  init();
})();

