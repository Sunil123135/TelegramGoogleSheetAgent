# Getting Started with RAG Highlighter

Welcome! This guide will help you get your private semantic search extension up and running in **under 15 minutes**.

## 📋 What You'll Need

- Google Chrome browser
- Google Colab account (free)
- 5-10 minutes to capture some pages
- 5 minutes to build your index on Colab

## 🚀 Quick Start (3 Steps)

### Step 1: Install the Extension (2 minutes)

1. Open Chrome and navigate to `chrome://extensions/`
2. Toggle **Developer mode** ON (top-right corner)
3. Click **Load unpacked**
4. Navigate to and select the `chrome_ext` folder
5. You should see "RAG Highlighter" with a 🔍 icon

**✅ Checkpoint**: Click the extension icon. You should see a popup with "Pages Captured: 0"

---

### Step 2: Capture Some Pages (5 minutes)

Just browse normally! Visit 5-10 interesting pages like:

- Wikipedia articles
- Documentation sites
- News articles
- Blog posts
- Stack Overflow threads

**What gets captured**: URL, title, and clean text (up to 8,000 characters)

**What gets skipped**: Gmail, WhatsApp, banking sites, login pages (see full list in `chrome_ext/DECISION.js`)

**💡 Tip**: Open the browser console (F12) and look for `[PERCEPTION] Page captured:` messages to verify capturing is working.

**✅ Checkpoint**: Click the extension icon. "Pages Captured" should be 5-10+

---

### Step 3: Build Your Search Index (5 minutes)

#### 3A. Export Your Pages

1. Click the extension icon
2. Click **"📥 Export pages.json"**
3. Save the file to your Downloads folder

#### 3B. Open Google Colab

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Create a new notebook
3. Copy/paste the code from `chrome_ext/tools/colab_index_build.md` cell by cell
4. Or upload the markdown file and run it as a notebook

#### 3C. Run the Notebook

Execute each cell in order:

```
Cell 1: Install dependencies (30 seconds)
Cell 2: Upload pages.json (10 seconds)
Cell 3: Chunk text (5 seconds)
Cell 4: Generate embeddings (60-120 seconds)
Cell 5: Normalize vectors (5 seconds)
Cell 6: Validate with FAISS (optional, 5 seconds)
Cell 7: Export bundle (5 seconds)
Cell 8: Download files (10 seconds)
```

**⚠️ Important**: You may need a Nomic API key. Get one free at [atlas.nomic.ai](https://atlas.nomic.ai)

#### 3D. Import the Bundle

1. Download `vectors.bin` and `meta.json` from Colab
2. Copy both files into `chrome_ext/bundle/`
3. Go to `chrome://extensions` and click the **refresh** icon on RAG Highlighter

**✅ Checkpoint**: Click extension icon. "Index Status" should show "✓ Loaded (N chunks, dim=768)"

---

## 🎯 Your First Search

1. Click the extension icon
2. Type a query like: `"machine learning basics"`
3. Click **Search**
4. Click any result
5. **Magic!** 🎉 The page opens and the matching text is highlighted

---

## 🎨 What Just Happened?

You built a **private semantic search engine** that:

- Runs 100% locally (no external API calls)
- Searches by meaning, not just keywords
- Opens pages and highlights exact matches
- Protects your privacy (skips sensitive sites)

---

## 📊 System Architecture

```
┌─────────────┐
│  PERCEPTION │ ← Captures pages while you browse
└──────┬──────┘
       ↓
┌─────────────┐
│  DECISION   │ ← Applies skip list and policies
└──────┬──────┘
       ↓
┌─────────────┐
│   AGENT     │ ← Stores pages, manages export
└──────┬──────┘
       ↓
   pages.json → Colab → vectors.bin + meta.json
                          ↓
                    ┌─────────────┐
                    │   MEMORY    │ ← Loads bundle, searches
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │   ACTION    │ ← Opens page + highlights
                    └─────────────┘
```

---

## 💡 Usage Tips

### For Best Results

- **Capture 50-100+ pages** for a useful knowledge base
- **Use specific queries** like "how to optimize React performance"
- **Click different results** to see which match best
- **Rebuild index weekly** as you browse more pages

### Managing Your Data

- **Export regularly**: Backup your pages.json
- **Clear old pages**: Use "🗑️ Clear Pages" to start fresh
- **Share bundles**: Copy bundle/ folder to share with team

### Customization

- **Skip list**: Edit `chrome_ext/DECISION.js` → `SKIP_DOMAINS`
- **Chunk size**: Modify in Colab notebook (default 800 chars)
- **Embedding model**: Change `MODEL_NAME` in Colab

---

## 🐛 Troubleshooting

### "Pages Captured: 0" not increasing

- Check console for `[PERCEPTION]` logs
- Make sure you're not on a skipped domain (Gmail, etc.)
- Wait 2 seconds after page loads (debounce delay)

### "Index Status: ⚠ Not Found"

- You haven't built the bundle yet (see Step 3)
- Bundle files not in `chrome_ext/bundle/`
- Bundle files corrupted (re-download from Colab)

### Search returns no results

- Bundle doesn't match your captured pages
- Try a different query (use lexical keywords)
- Rebuild index with more pages

### Highlighting doesn't work

- Page may block content scripts (CSP policy)
- Try clicking result again
- Check console for `[PERCEPTION]` errors

---

## 📚 Next Steps

### Beginner
- ✅ Complete the 3-step quick start
- ✅ Capture 50+ pages
- ✅ Try 10 different searches
- ✅ Read `chrome_ext/README.md` for details

### Intermediate
- 📖 Read `chrome_ext/ARCHITECTURE.md` to understand the design
- 🔧 Customize the skip list for your needs
- 📊 Try different chunk sizes in Colab
- 🔬 Experiment with search queries

### Advanced
- 🧠 Swap the embedder (integrate transformers.js)
- 🗜️ Add PCA compression to reduce bundle size
- 📦 Implement sharded bundles for large corpora
- 🔄 Add incremental indexing
- 🌐 Contribute to the project!

---

## 🤝 Getting Help

- **Documentation**: See `chrome_ext/README.md`
- **Architecture**: See `chrome_ext/ARCHITECTURE.md`
- **Installation**: See `chrome_ext/INSTALL.md`
- **Colab Guide**: See `chrome_ext/tools/colab_index_build.md`
- **Issues**: Check console logs and extension errors

---

## 🎓 Learning Resources

### Understanding RAG
- What is RAG? Retrieval-Augmented Generation explained
- How semantic search works
- Vector embeddings basics

### Chrome Extensions
- Manifest V3 documentation
- Content scripts vs service workers
- Chrome Storage API

### Machine Learning
- Text embeddings (nomic, OpenAI, etc.)
- Cosine similarity
- FAISS vector search

---

## ✨ Success Story

Here's what you should be able to do after completing this guide:

1. ✅ **Capture** pages automatically while browsing
2. ✅ **Export** your browsing history as structured data
3. ✅ **Build** a semantic search index with embeddings
4. ✅ **Search** using natural language queries
5. ✅ **Highlight** exact matches on original pages
6. ✅ **Understand** the 5-layer architecture
7. ✅ **Customize** for your specific needs

---

## 🏆 Challenge: Build Your Knowledge Base

**Goal**: Create a personal knowledge base of 100+ pages and make it searchable

1. Pick a topic you're learning (e.g., "Python data science")
2. Browse 100+ relevant pages over the next week
3. Export and build your index
4. Use it as your personal documentation assistant
5. Share your results!

**Bonus**: Calculate your "knowledge graph" statistics:
- Total pages captured
- Most common domains
- Average text length
- Search success rate

---

## 🚀 You're Ready!

You now have a **private, local-first semantic search engine** that works entirely in your browser. No external APIs, no privacy concerns, no subscription fees.

**Go ahead and start building your knowledge base!** 🎉

---

**Questions?** See the documentation in `chrome_ext/` or check the verification checklist in `chrome_ext/VERIFICATION_CHECKLIST.md`.

**Happy searching!** 🔍

