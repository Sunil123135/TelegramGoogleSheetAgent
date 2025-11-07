# Google Colab Notebook: Build RAG Index Bundle

This is a step-by-step guide to build your semantic search index on Google Colab.

Copy each code cell into a new Colab notebook in order.

---

## Cell 1: Install Dependencies

```python
!pip -q install faiss-cpu nomic numpy tqdm
```

---

## Cell 2: Upload pages.json

```python
from google.colab import files
import json
import numpy as np

# Upload your pages.json file
uploaded = files.upload()

# Load the JSON data
pages = json.loads(list(uploaded.values())[0].decode('utf-8'))

print(f"✓ Loaded {len(pages)} pages")
print(f"Sample keys: {list(pages[0].keys()) if pages else []}")
```

**Expected output**: Shows number of pages and keys like `['url', 'title', 'text', 'ts']`

---

## Cell 3: Chunk Text

```python
import re

def chunk_text(text, size=800, overlap=120):
    """Split text into overlapping chunks"""
    text = re.sub(r"\s+", " ", text.strip())
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += max(1, size - overlap)
    return chunks

# Create chunks
rows = []
for page in pages:
    page_chunks = chunk_text(page["text"])
    for chunk in page_chunks:
        rows.append({
            "url": page["url"],
            "title": page["title"],
            "chunk_text": chunk
        })

print(f"✓ Created {len(rows)} chunks from {len(pages)} pages")
print(f"Average chunks per page: {len(rows) / len(pages):.1f}")
```

---

## Cell 4: Generate Embeddings

```python
from nomic import embed
import os

# Configuration
EMBED_DIM = 768  # nomic-embed-text-v1.5 dimension
MODEL_NAME = "nomic-embed-text-v1.5"

# You may need to set your Nomic API key
# Get it from: https://atlas.nomic.ai/
# os.environ["NOMIC_API_KEY"] = "your_key_here"

# Extract texts
texts = [r["chunk_text"] for r in rows]

print(f"Embedding {len(texts)} chunks...")
print(f"This may take a few minutes...")

# Generate embeddings
result = embed.text(
    texts,
    model=MODEL_NAME,
    task_type="search_document"
)

# Convert to numpy array
X = np.array(result['embeddings'], dtype=np.float32)

print(f"✓ Generated embeddings: {X.shape}")
print(f"  Vectors: {X.shape[0]}")
print(f"  Dimensions: {X.shape[1]}")

# Verify dimension
assert X.shape[1] == EMBED_DIM, f"Dimension mismatch: expected {EMBED_DIM}, got {X.shape[1]}"
```

---

## Cell 5: L2 Normalization

```python
# L2-normalize vectors for cosine similarity via dot product
norms = np.linalg.norm(X, axis=1, keepdims=True)
X = X / (norms + 1e-12)

# Ensure float32
X = X.astype(np.float32)

print(f"✓ Normalized vectors: {X.shape}")
print(f"Sample norm (should be ~1.0): {np.linalg.norm(X[0]):.6f}")
```

---

## Cell 6: Validate with FAISS (Optional)

```python
import faiss

# Create FAISS index (Inner Product = cosine for normalized vectors)
index = faiss.IndexFlatIP(EMBED_DIM)
index.add(X)

print(f"✓ FAISS index built: {index.ntotal} vectors")

# Test search on first 5 vectors
D, I = index.search(X[:5], k=5)

print("\nValidation: Top-5 similar to first 5 vectors")
print("(First result should be self with similarity ~1.0)")
for i in range(5):
    print(f"Query {i}: scores = {D[i][:3]} | indices = {I[i][:3]}")
```

**Expected**: First score should be ~1.0 (self-similarity)

---

## Cell 7: Export Bundle

```python
import os
import json

# Create bundle directory
os.makedirs("bundle", exist_ok=True)

# Write vectors.bin
with open("bundle/vectors.bin", "wb") as f:
    X.tofile(f)

print(f"✓ Wrote vectors.bin ({X.nbytes / 1024 / 1024:.1f} MB)")

# Write meta.json
meta = []
for i, row in enumerate(rows):
    meta.append({
        "id": i,
        "url": row["url"],
        "title": row["title"],
        "chunk_text": row["chunk_text"]
    })

with open("bundle/meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"✓ Wrote meta.json ({len(meta)} entries)")
```

---

## Cell 8: Download Bundle

```python
from google.colab import files

# Download the bundle files
print("Downloading vectors.bin...")
files.download("bundle/vectors.bin")

print("Downloading meta.json...")
files.download("bundle/meta.json")

print("\n✓ Bundle ready!")
print("\nNext steps:")
print("1. Create chrome_ext/bundle/ folder in your extension directory")
print("2. Copy both files into chrome_ext/bundle/")
print("3. Reload the extension in chrome://extensions")
print("4. Open the popup and search!")
```

---

## Summary

You now have:
- `vectors.bin` — Float32 array (N × D), L2-normalized
- `meta.json` — Metadata array with N entries

**File sizes**:
- `vectors.bin`: N × 768 × 4 bytes (e.g., 1000 chunks = ~3 MB)
- `meta.json`: Depends on text length (usually similar size)

**Next**: Import these files into your extension and start searching!

