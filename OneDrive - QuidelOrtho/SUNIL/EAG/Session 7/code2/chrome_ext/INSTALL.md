# Quick Installation Guide

## Step 1: Load the Extension

1. Open Google Chrome
2. Navigate to `chrome://extensions/`
3. Enable **Developer mode** (toggle in top-right corner)
4. Click **Load unpacked**
5. Select the `chrome_ext` folder
6. The RAG Highlighter extension should now appear in your toolbar

## Step 2: Verify Installation

- Click the extension icon (magnifying glass)
- You should see the popup with:
  - Pages Captured: 0
  - Index Status: ⚠ Not Found
  - Search box
  - Export/Clear buttons

## Step 3: Start Capturing Pages

Just browse normally! The extension will automatically capture pages **except**:
- Gmail / Google Mail
- WhatsApp
- Banking sites
- Login/auth pages
- Other confidential domains (see DECISION.js for full list)

## Step 4: Export and Build Index

Once you've captured some pages:

1. Click **Export pages.json** in the popup
2. Save the file
3. Open Google Colab
4. Follow the notebook in `tools/colab_index_build.md`
5. Download `vectors.bin` and `meta.json`
6. Place them in `chrome_ext/bundle/`
7. Reload the extension

## Step 5: Search!

1. Click the extension icon
2. Type a query in the search box
3. Click **Search**
4. Click any result to open the page and see the highlighted text

---

## Troubleshooting

### Extension won't load
- Check that manifest.json is valid
- Ensure all .js files are in chrome_ext/
- Look for errors in `chrome://extensions/` (click "Errors" button)

### No pages captured
- Check if you're visiting skipped domains
- Open Developer Tools → Console and look for [PERCEPTION] logs
- Verify the content script is loading

### Search shows "Bundle not found"
- You need to build the index first (see Step 4)
- Verify `bundle/vectors.bin` and `bundle/meta.json` exist
- Check file sizes (vectors.bin should be N × 768 × 4 bytes)

### Highlighting doesn't work
- The content script needs permission to access the page
- Check the URL isn't blocked by CSP
- Look for [PERCEPTION] logs in the page's console

### Service worker errors
- MV3 service workers can go to sleep
- Open `chrome://extensions/` → click "Service worker" link to wake it
- Check for errors in the service worker console

---

## Permissions Explained

- **storage**: Store captured pages locally
- **tabs**: Open search results in new tabs
- **activeTab**: Access current page for highlighting
- **scripting**: Inject highlight script
- **host_permissions**: Run content script on all HTTP/HTTPS pages

All permissions are used locally - **no data leaves your machine**.

---

## Next Steps

- Capture 50-100 pages for a useful index
- Experiment with different search queries
- Customize the skip list in DECISION.js
- Try different embedding models in Colab

Enjoy your private semantic search! 🔍

