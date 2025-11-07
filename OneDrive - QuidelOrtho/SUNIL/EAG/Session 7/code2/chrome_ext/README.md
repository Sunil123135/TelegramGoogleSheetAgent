# RAG Highlighter — Private, Local RAG with On-Page Highlighting

This Chrome extension builds a **private semantic search** over pages you browse and lets you **open the source page and auto-highlight** the matched passage.

- **PERCEPTION**: Captures page text as you browse (skips confidential domains).
- **MEMORY**: Loads a portable bundle (`bundle/vectors.bin` + `bundle/meta.json`) built on Google Colab using **nomic** embeddings and **FAISS** for validation.
- **ACTION**: Popup search → open source URL → highlight best matching snippet.
- **DECISION**: Policies for skip list, capture size, debounce, and fallbacks.
- **AGENT**: Background orchestrator for messaging, export/import, navigation.

---

## 0) Requirements

- Chrome (or Chromium-based browser)
- (Optional) Google Colab account for building the index bundle
- ~50–200 MB free disk for index bundle (depends on corpus size & embedding dim)

---

## 1) Install the Extension (Developer Mode)

1. Open `chrome://extensions` → enable **Developer mode**
2. Click **Load unpacked** → select the `chrome_ext/` folder
3. You should see **RAG Highlighter** appear in your toolbar

> **Note**: The extension ships with an empty bundle by default. You'll add your own.

---

## 2) Capture Pages While You Browse

By default the content script runs on `https://*/*` and `http://*/*` **except** skip domains:
- `gmail.com`, `mail.google.com`, `whatsapp.com`, `web.whatsapp.com`,
- `accounts.google.com`, known net-banking portals, and a configurable keyword list.

**What is captured?**
- `url`, `title`, and a cleaned `text` (up to ~8,000 chars)
- **No** network calls are made. Data is stored locally in extension storage.

### Export your crawl

1. Open the extension popup
2. Click **Export pages.json**
3. Save the file locally — you'll upload it to Colab to build the index bundle

---

## 3) Build the Index on Google Colab

Open a new Colab notebook and run the following steps. (Or open `tools/colab_index_build.ipynb` as your reference notebook.)

### A) Install dependencies

```python
!pip -q install faiss-cpu nomic numpy tqdm
```

### B) Upload your pages.json

```python
from google.colab import files
uploaded = files.upload()  # choose pages.json
import json, numpy as np
pages = json.loads(list(uploaded.values())[0].decode('utf-8'))
print(f"Loaded {len(pages)} pages")
print("Sample keys:", list(pages[0].keys()) if pages else [])
```

Expected keys per item: `{"url","title","text","ts"}`.

### C) Chunking

```python
import re

def chunk_text(t, size=800, overlap=120):
    t = re.sub(r"\s+", " ", t.strip())
    out, i = [], 0
    while i < len(t):
        out.append(t[i:i+size])
        i += max(1, size - overlap)
    return out

rows = []
for p in pages:
    for ch in chunk_text(p["text"]):
        rows.append({"url": p["url"], "title": p["title"], "chunk_text": ch})

print(f"Created {len(rows)} chunks")
```

### D) Embeddings (nomic)

```python
from nomic import embed

EMBED_DIM = 768   # set to your model's dimensionality
MODEL_NAME = "nomic-embed-text-v1.5"  # example; pick any supported model

texts = [r["chunk_text"] for r in rows]
print(f"Embedding {len(texts)} chunks...")

embs = embed.text(texts, model=MODEL_NAME, task_type="search_document")
X = np.array(embs['embeddings'], dtype=np.float32)

assert X.shape[1] == EMBED_DIM, f"Dimension mismatch: {X.shape}"

# L2-normalize
X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
X = X.astype(np.float32)

print(f"Embeddings shape: {X.shape}")
```

### E) (Optional) Validate neighbors with FAISS

```python
import faiss

index = faiss.IndexFlatIP(EMBED_DIM)
index.add(X)
D, I = index.search(X[:5], k=5)  # sanity check

print("Sample similarities:", D[0])
print("Sample indices:", I[0])
```

### F) Export the index bundle

```python
import os

os.makedirs("bundle", exist_ok=True)

# Write vectors
X.tofile("bundle/vectors.bin")

# Write metadata
meta = [
    {
        "id": i,
        "url": r["url"],
        "title": r["title"],
        "chunk_text": r["chunk_text"]
    }
    for i, r in enumerate(rows)
]

with open("bundle/meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"Exported bundle: {len(meta)} vectors")
```

### G) Download the files

```python
from google.colab import files

files.download("bundle/vectors.bin")
files.download("bundle/meta.json")
```

You now have:
- `vectors.bin` — Float32 row-stacked, L2-normalized embeddings
- `meta.json` — parallel metadata with id, url, title, chunk_text

---

## 4) Import the Bundle into the Extension

1. Create folder `chrome_ext/bundle/` if it doesn't exist
2. Copy `vectors.bin` + `meta.json` into `chrome_ext/bundle/`
3. Refresh the extension on `chrome://extensions`

---

## 5) Use Semantic Search + Auto-Highlight

1. Click the extension icon to open the popup
2. Type a query and press **Search**
3. Click a result → the extension opens that URL
4. The page auto-highlights the best matching snippet and scrolls to it

### How highlighting works

- The popup appends a `#ragq=...` anchor when opening a result
- The content script reads `ragq`, finds the best fuzzy match window (±200 chars), wraps it in `<mark class="rag-highlight">`, injects CSS, and calls `element.scrollIntoView({block:'center'})`

---

## 6) Troubleshooting & Fallbacks

### Bundle missing or dimension mismatch

The popup shows an "Import bundle" banner. Verify that:
- `vectors.bin` length is N × D × 4 bytes
- `len(meta.json)` == N

### No results

The extension relaxes to lexical overlap search; if still empty, export more pages and rebuild the bundle.

### Highlight fails

The extension falls back to the first literal occurrence and draws a soft overlay.

---

## 7) Architecture Map

- **PERCEPTION** (`PERCEPTION.js`): capture + clean text; skip confidential domains; queue to local storage; supports export.
- **MEMORY** (`MEMORY.js`): load bundle; cosine top-K; dimension checks.
- **ACTION** (`ACTION.js`): query embedding stub (swappable), blend semantic + lexical, open URL with `#ragq`, highlight in content script.
- **DECISION** (`DECISION.js`): policies (skip list, debounce, size caps), fallback selection.
- **AGENT** (`AGENT.js`): background routing; export/import; open + focus tabs.

---

## 8) Roadmap

- Swap embedder stub with transformers.js / ONNX Runtime Web
- Add PCA to compress vectors (e.g., 768→384) before writing `vectors.bin`
- Sharded bundles for very large corpora
- Team-share bundles over shared drives

---

## 9) Privacy & Security

- **No external calls** from the extension (all processing is local)
- **User controls export**: You choose when to export `pages.json`
- **Bundle is local-only**: `vectors.bin` and `meta.json` stay on your machine
- **Skip list**: Automatically excludes sensitive domains (Gmail, banking, etc.)

---

## 10) License

MIT License - feel free to modify and share!

---

## 11) Contributing

Pull requests welcome! Please ensure:
- Code follows the 5-layer architecture
- All reasoning is tagged (`[arch]`, `[algo]`, `[io]`, `[perf]`, `[security]`, `[error]`)
- Tests pass (if you add them)

---

**Built with ❤️ for private, local-first semantic search**

