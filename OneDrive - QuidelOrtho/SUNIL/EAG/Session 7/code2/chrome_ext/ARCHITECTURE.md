# Architecture Documentation

## 5-Layer Architecture

This extension implements a **5-layer cognitive architecture** for building a private RAG system:

### 1. PERCEPTION Layer (`PERCEPTION.js`)

**Role**: Sense and capture the external environment

**Implementation**:
- Content script that runs on every webpage
- Extracts clean text from `document.body.textContent`
- Applies DECISION policies to skip confidential domains
- Debounces captures to avoid rapid-fire on dynamic pages
- Sends captured data to AGENT layer via `chrome.runtime.sendMessage`
- Listens for highlight requests via URL hash (`#ragq=...`)

**Key Functions**:
- `extractPageText()` — DOM text extraction
- `capturePage()` — Capture and send to background
- `checkForHighlight()` — Detect highlight requests
- `highlightSnippet()` — Wrap matching text in `<mark>`

**Tags**: `[io]`, `[algo]`, `[perf]`, `[ux]`

---

### 2. MEMORY Layer (`MEMORY.js`)

**Role**: Store and retrieve knowledge

**Implementation**:
- Loads binary vector bundle (`vectors.bin`) and metadata (`meta.json`)
- Performs in-browser cosine similarity search
- Uses Float32 typed arrays for performance
- Implements L2 normalization
- Provides hybrid search (semantic + lexical fallback)

**Key Functions**:
- `loadBundle()` — Load vectors.bin + meta.json
- `embedQuery()` — Simple char-bag embedder stub
- `search()` — Top-K cosine similarity
- `lexicalSearch()` — Keyword fallback
- `hybridSearch()` — Blend semantic + lexical

**Data Structures**:
- `vectors`: Float32Array (N × D)
- `meta`: Array of {id, url, title, chunk_text}

**Tags**: `[algo]`, `[perf]`, `[io]`, `[error]`

---

### 3. DECISION Layer (`DECISION.js`)

**Role**: Apply policies and constraints

**Implementation**:
- Centralized policy configuration
- Skip lists for confidential domains
- Size limits and validation rules
- Fallback strategies

**Key Policies**:
- `SKIP_DOMAINS`: Gmail, WhatsApp, banking, auth sites
- `MAX_TEXT_LENGTH`: 8000 chars per page
- `DEBOUNCE_DELAY`: 2000ms before capture
- `MIN_TEXT_LENGTH`: 100 chars minimum

**Key Functions**:
- `shouldSkipUrl()` — Domain filtering
- `cleanText()` — Text normalization
- `isValidText()` — Validation
- `getMissingBundleMessage()` — Error messaging

**Tags**: `[decision]`, `[security]`, `[error]`

---

### 4. ACTION Layer (`ACTION.js`)

**Role**: Execute actions in the world

**Implementation**:
- Processes search queries
- Formats search results
- Opens URLs with highlight anchors
- Sends highlight commands to content scripts

**Key Functions**:
- `processQuery()` — End-to-end query handling
- `extractSnippet()` — Context window around matches
- `openAndHighlight()` — Open tab + trigger highlight
- `scoreSnippet()` — Relevance scoring

**Tags**: `[action]`, `[algo]`, `[io]`

---

### 5. AGENT Layer (`AGENT.js`)

**Role**: Orchestrate all layers

**Implementation**:
- Service worker (background script)
- Message routing hub
- Storage management
- Export/import coordination

**Key Functions**:
- `handleCapturePage()` — Store captured pages
- `handleExportPages()` — Download pages.json
- `handleGetStats()` — Query storage stats
- `handleClearPages()` — Delete all pages

**Message Types**:
- `CAPTURE_PAGE` — From PERCEPTION
- `EXPORT_PAGES` — From popup
- `GET_STATS` — From popup
- `SEARCH_QUERY` — From popup (logged)

**Tags**: `[agent]`, `[io]`, `[arch]`

---

## Data Flow

### Capture Flow

```
User browses page
    ↓
PERCEPTION: Extract text
    ↓
DECISION: Check skip policies
    ↓ (if allowed)
AGENT: Store in chrome.storage.local
```

### Export Flow

```
User clicks "Export"
    ↓
AGENT: Load from storage
    ↓
AGENT: Create JSON blob
    ↓
AGENT: Trigger download
```

### Search Flow

```
User types query in popup
    ↓
ACTION: processQuery()
    ↓
MEMORY: Load bundle (if needed)
    ↓
MEMORY: embedQuery() → vector
    ↓
MEMORY: hybridSearch() → results
    ↓
ACTION: Format results
    ↓
Popup: Display results
    ↓
User clicks result
    ↓
ACTION: openAndHighlight()
    ↓
AGENT: Create/focus tab
    ↓
PERCEPTION: Detect #ragq=...
    ↓
PERCEPTION: highlightSnippet()
```

---

## File Manifest

| File | Layer | Purpose |
|------|-------|---------|
| `manifest.json` | Config | Chrome MV3 manifest |
| `PERCEPTION.js` | L1 | Content script (capture + highlight) |
| `MEMORY.js` | L2 | Vector search engine |
| `DECISION.js` | L3 | Policies and constraints |
| `ACTION.js` | L4 | Query processing + actions |
| `AGENT.js` | L5 | Service worker orchestrator |
| `popup.html` | UI | Extension popup interface |
| `popup.js` | UI | Popup logic |
| `styles.css` | UI | Styling |

---

## Extension to Extension Communication

```
Content Script (PERCEPTION)
    ↕ chrome.runtime.sendMessage()
Service Worker (AGENT)
    ↕ chrome.runtime.sendMessage()
Popup (UI + ACTION + MEMORY)
```

---

## Security Model

- **No external network calls** from extension
- **Local-only processing** (vectors, search)
- **User-controlled export** (pages.json)
- **Skip confidential domains** (DECISION policies)
- **Content Security Policy** compliant

---

## Performance Considerations

- **Debouncing**: 2s delay before capture
- **Text limits**: Max 8KB per page
- **Typed arrays**: Float32Array for vectors
- **Cosine via dot product**: Assumes L2-normalized vectors
- **Lazy bundle loading**: Only load when searching

---

## Future Enhancements

1. **Better embeddings**: Swap char-bag with transformers.js or ONNX Runtime Web
2. **PCA compression**: Reduce 768 → 384 dimensions
3. **Incremental indexing**: Add new pages without full rebuild
4. **Sharded bundles**: Support large corpora (>100K pages)
5. **Chrome Sync**: Optionally sync bundles across devices
6. **Advanced highlighting**: Multi-color, annotations, history

---

## Reasoning Tags

Code comments use reasoning tags to explain decisions:

- `[arch]` — Architecture/design decisions
- `[algo]` — Algorithm choices
- `[io]` — I/O operations
- `[perf]` — Performance optimizations
- `[security]` — Security considerations
- `[error]` — Error handling
- `[ux]` — User experience choices
- `[decision]` — Policy decisions

Example:
```javascript
// [perf] Use Float32Array for fast vector operations
this.vectors = new Float32Array(vectorsBuffer);
```

---

## Testing Strategy

1. **Unit Tests**: Test individual functions (embedQuery, cosineSimilarity, etc.)
2. **Integration Tests**: Test message passing between layers
3. **E2E Tests**: Capture → Export → Build → Search → Highlight
4. **Performance Tests**: Benchmark search on 10K+ vectors
5. **Security Tests**: Verify skip list, no network calls

---

## Contributing

When modifying the code:

1. **Maintain layer separation**: Don't mix concerns
2. **Use reasoning tags**: Explain your choices
3. **Update documentation**: Keep this file in sync
4. **Follow conventions**: Match existing code style
5. **Test thoroughly**: All 5 layers must work together

---

Built with ❤️ for private, local-first semantic search

