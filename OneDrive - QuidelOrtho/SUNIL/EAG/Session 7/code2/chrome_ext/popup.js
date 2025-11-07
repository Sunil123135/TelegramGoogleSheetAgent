// popup.js — UI logic for the extension popup
// [ux] Handles user interactions, displays results, manages state

document.addEventListener('DOMContentLoaded', async () => {
  console.log('[POPUP] Initializing...');
  
  // [io] Get DOM elements
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const resultsContainer = document.getElementById('resultsContainer');
  const exportBtn = document.getElementById('exportBtn');
  const clearBtn = document.getElementById('clearBtn');
  const pageCountEl = document.getElementById('pageCount');
  const indexStatusEl = document.getElementById('indexStatus');

  // [state] Current search state
  let isSearching = false;

  // [arch] Initialize
  await init();

  // [ux] Event listeners
  searchBtn.addEventListener('click', handleSearch);
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
  });
  exportBtn.addEventListener('click', handleExport);
  clearBtn.addEventListener('click', handleClear);

  // [arch] Initialize popup state
  async function init() {
    await updateStats();
    await loadBundle();
  }

  // [io] Update statistics display
  async function updateStats() {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'GET_STATS' });
      if (response.success) {
        pageCountEl.textContent = response.stats.pageCount;
      }
    } catch (error) {
      console.error('[POPUP] Error updating stats:', error);
      pageCountEl.textContent = 'Error';
    }
  }

  // [io] Load search bundle
  async function loadBundle() {
    try {
      indexStatusEl.textContent = 'Loading...';
      const result = await MEMORY.loadBundle();
      
      if (result.success) {
        indexStatusEl.textContent = `✓ Loaded (${result.count} chunks, dim=${result.dim})`;
        indexStatusEl.style.color = '#4caf50';
      } else {
        indexStatusEl.textContent = '⚠ Not Found';
        indexStatusEl.style.color = '#ff9800';
        showBundleHelp();
      }
    } catch (error) {
      console.error('[POPUP] Error loading bundle:', error);
      indexStatusEl.textContent = '⚠ Error';
      indexStatusEl.style.color = '#f44336';
      showBundleHelp();
    }
  }

  // [ux] Show help message for missing bundle
  function showBundleHelp() {
    resultsContainer.innerHTML = `
      <div class="message message-warning">
        <strong>⚠️ Index Bundle Not Found</strong>
        <p>To enable search:</p>
        <ol style="text-align: left; margin: 10px 0; padding-left: 20px;">
          <li>Export your pages using the button below</li>
          <li>Follow the Colab steps in README.md to build the index</li>
          <li>Place vectors.bin + meta.json in chrome_ext/bundle/</li>
          <li>Reload this extension</li>
        </ol>
      </div>
    `;
  }

  // [action] Handle search
  async function handleSearch() {
    if (isSearching) return;
    
    const query = searchInput.value.trim();
    if (!query) {
      showMessage('Please enter a search query', 'warning');
      return;
    }

    isSearching = true;
    searchBtn.textContent = 'Searching...';
    searchBtn.disabled = true;

    try {
      // [action] Process query
      const result = await ACTION.processQuery(query, 10);
      
      if (!result.success) {
        if (result.needsBundle) {
          showBundleHelp();
        } else {
          showMessage(result.error, 'error');
        }
        return;
      }

      // [ux] Display results
      if (result.results.length === 0) {
        showMessage(result.message || 'No results found', 'info');
      } else {
        displayResults(result.results, query);
      }
    } catch (error) {
      console.error('[POPUP] Search error:', error);
      showMessage('Search failed: ' + error.message, 'error');
    } finally {
      isSearching = false;
      searchBtn.textContent = 'Search';
      searchBtn.disabled = false;
    }
  }

  // [ux] Display search results
  function displayResults(results, query) {
    resultsContainer.innerHTML = '';
    
    const header = document.createElement('div');
    header.className = 'results-header';
    header.textContent = `Found ${results.length} result${results.length !== 1 ? 's' : ''}`;
    resultsContainer.appendChild(header);

    results.forEach((result, index) => {
      const resultEl = document.createElement('div');
      resultEl.className = 'result-item';
      
      // [ux] Build result HTML
      resultEl.innerHTML = `
        <div class="result-header">
          <div class="result-title">${escapeHtml(result.title)}</div>
          <div class="result-score">${Math.round(result.score * 100)}%</div>
        </div>
        <div class="result-url">${escapeHtml(result.url)}</div>
        <div class="result-snippet">${highlightQuery(escapeHtml(result.snippet), query)}</div>
      `;
      
      // [action] Click to open and highlight
      resultEl.addEventListener('click', () => {
        handleResultClick(result);
      });
      
      resultsContainer.appendChild(resultEl);
    });
  }

  // [action] Handle result click
  async function handleResultClick(result) {
    console.log('[POPUP] Opening result:', result.url);
    
    try {
      await ACTION.openAndHighlight(result.url, result.fullText);
      // [ux] Optional: close popup after opening
      // window.close();
    } catch (error) {
      console.error('[POPUP] Error opening result:', error);
      showMessage('Failed to open page', 'error');
    }
  }

  // [io] Handle export
  async function handleExport() {
    exportBtn.disabled = true;
    exportBtn.textContent = 'Exporting...';
    
    try {
      const response = await chrome.runtime.sendMessage({ type: 'EXPORT_PAGES' });
      
      if (response.success) {
        showMessage(`Exported ${response.count} pages`, 'success');
      } else {
        showMessage('Export failed: ' + response.error, 'error');
      }
    } catch (error) {
      console.error('[POPUP] Export error:', error);
      showMessage('Export failed', 'error');
    } finally {
      exportBtn.disabled = false;
      exportBtn.textContent = '📥 Export pages.json';
    }
  }

  // [io] Handle clear
  async function handleClear() {
    if (!confirm('Are you sure you want to clear all captured pages? This cannot be undone.')) {
      return;
    }

    clearBtn.disabled = true;
    clearBtn.textContent = 'Clearing...';
    
    try {
      const response = await chrome.runtime.sendMessage({ type: 'CLEAR_PAGES' });
      
      if (response.success) {
        showMessage('All pages cleared', 'success');
        await updateStats();
      } else {
        showMessage('Clear failed: ' + response.error, 'error');
      }
    } catch (error) {
      console.error('[POPUP] Clear error:', error);
      showMessage('Clear failed', 'error');
    } finally {
      clearBtn.disabled = false;
      clearBtn.textContent = '🗑️ Clear Pages';
    }
  }

  // [ux] Show message
  function showMessage(text, type = 'info') {
    resultsContainer.innerHTML = `
      <div class="message message-${type}">
        ${escapeHtml(text)}
      </div>
    `;
  }

  // [security] Escape HTML
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // [ux] Highlight query terms in snippet
  function highlightQuery(text, query) {
    const words = query.toLowerCase().split(/\s+/);
    let result = text;
    
    words.forEach(word => {
      if (word.length < 2) return;
      const regex = new RegExp(`(${escapeRegex(word)})`, 'gi');
      result = result.replace(regex, '<mark>$1</mark>');
    });
    
    return result;
  }

  // [algo] Escape regex special characters
  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
});

