# Bundle Directory

Place your index bundle files here:
- `vectors.bin` - Float32 binary file with L2-normalized embeddings
- `meta.json` - JSON array with metadata for each vector

## File Format

### vectors.bin
- Binary file containing N × D float32 values
- N = number of chunks
- D = embedding dimension (e.g., 768 for nomic-embed-text-v1.5)
- Vectors are L2-normalized for cosine similarity
- Total size: N × D × 4 bytes

### meta.json
- JSON array with N objects
- Each object has:
  - `id`: integer (0 to N-1)
  - `url`: source page URL
  - `title`: page title
  - `chunk_text`: the text chunk for this embedding

## How to Generate

Follow the steps in `../README.md` section 3 to:
1. Export your `pages.json` from the extension
2. Upload to Google Colab
3. Run the notebook cells to generate embeddings
4. Download `vectors.bin` and `meta.json`
5. Place them in this directory
6. Reload the extension

## Empty Bundle

Until you generate your bundle, the extension will show a warning message with instructions.

