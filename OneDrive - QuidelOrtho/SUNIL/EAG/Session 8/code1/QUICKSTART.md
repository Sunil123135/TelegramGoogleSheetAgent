# Cursor Agent - Quick Start Guide

Get up and running in 5 minutes! ⚡

## What is This?

A production-ready AI agent for Cursor with:
- 🧠 **4-Layer Architecture**: Perception → Memory → Decision → Action
- 🔍 **Semantic Search**: FAISS + Nomic embeddings
- 🛠️ **8+ Tool Integrations**: Google Workspace, Telegram, web scraping
- 📊 **Smart Chunking**: Topic-aware semantic segmentation
- 🎯 **Multi-Step Planning**: Automatic task decomposition

## Install (30 seconds)

```bash
# Clone and install
cd <workspace>
uv pip install -e .

# Or with pip
pip install -e .

# Install Playwright for screenshots
playwright install chromium
```

## Configure (2 minutes)

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` with your details:**
   ```bash
   SELF_EMAIL=your@email.com
   # Add Google/Telegram credentials later
   
   # Optional: Configure a specific output Google Sheet
   F1_OUTPUT_SHEET_URL=https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY/edit?usp=drive_link
   F1_OUTPUT_SHEET_ID=1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY
   ```

## Run Your First Workflow (1 minute)

```bash
# Run the F1 standings example (uses mock Google APIs)
python main.py f1
```

Expected output:
```
============================================================
Cursor Agent - F1 Standings Workflow
============================================================

[MOCK] Created Google Sheet: F1_Current_Standings
[MOCK] Sheet URL: https://docs.google.com/spreadsheets/d/mock_...
[MOCK] Shared file mock_... with anyone as reader
[MOCK] Captured screenshot
[MOCK] Sent email to your@email.com

✅ Workflow completed successfully!

📋 Plan: 6 steps
  ✓ 1. Fetch F1 driver standings from web
  ✓ 2. Create Google Sheet with standings
  ✓ 3. Share sheet publicly
  ✓ 4. Capture screenshot of sheet
  ✓ 5. Email sheet link with screenshot
  ✓ 6. Send confirmation to Telegram

Completed 6/6 steps.
```

## Try Interactive Mode

```bash
python main.py interactive
```

Example conversation:
```
👤 You: Find Python news and summarize it

🤖 Agent: Processing...
✓ Successfully completed task
📊 Found 5 articles
📝 Summary saved

👤 You: memory

📚 Working Memory:
  Messages: 2/10
  Blackboard keys: ['extracted_content', 'summary']

👤 You: exit
👋 Goodbye!
```

## What Just Happened?

The agent:
1. **Perceived**: Extracted F1 standings from web → Markdown
2. **Decided**: Created 6-step execution plan
3. **Acted**: Called tools via MCP (Google Sheets, Gmail, etc.)
4. **Remembered**: Stored results in FAISS + scratchpad

## Next Steps

### 1. Set Up Real Google APIs (Optional)

For production use:

**Quick Setup**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable APIs (Sheets, Drive, Gmail)
3. Create OAuth credentials (Desktop app)
4. Download `client_secret.json`
5. Place in `~/.config/cursor-agent/google/`
6. Update `.env` paths

**Detailed Guide**: See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

### 2. Set Up Telegram (Optional)

1. Message [@BotFather](https://t.me/BotFather)
2. Create bot → copy token
3. Get chat ID from [@getidsbot](https://t.me/getidsbot)
4. Add to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### 3. Build Your Own Workflows

**Python API**:
```python
from agent.orchestrator import CursorAgent
import asyncio

async def main():
    agent = CursorAgent()
    
    # Simple message
    response = await agent.process_message(
        "Find the top Python packages and create a spreadsheet"
    )
    print(response)
    
    # Workflow with detailed results
    result = await agent.execute_workflow(
        "Summarize recent AI news and email it to me"
    )
    print(result["blackboard"])

asyncio.run(main())
```

**Add Custom Tools**:
1. Create MCP server in `mcp_servers/`
2. Add to `.cursor/mcp.json`
3. Update `agent/action/executor.py`
4. Use in workflows!

## Architecture at a Glance

```
USER INPUT
    ↓
┌─────────────────────────────────────┐
│      AGENT ORCHESTRATOR             │
└─────────────────────────────────────┘
    ↓           ↓           ↓
PERCEPTION   MEMORY    DECISION
    ↓           ↓           ↓
   Markdown   FAISS    Plan Graph
    ↓           ↓           ↓
        ↓       ↓       ↓
        └───────┴───────┘
                ↓
            ACTION
                ↓
        MCP Tool Calls
                ↓
            RESULTS
```

### Key Files

```
agent/
├── orchestrator.py      # Main agent loop
├── models.py           # Data models (Pydantic)
├── perception/         # Ingestion + chunking
├── memory/            # FAISS + scratchpad
├── decision/          # Planning + tool selection
└── action/            # Tool execution

mcp_servers/           # MCP integrations
├── trafilatura_stdio.py
├── google_sheets_stdio.py
└── ... (8 total)

main.py               # Entry point
```

## Common Workflows

### 1. Web Research → Summary → Email

```python
goal = "Research Rust programming, create a summary doc, and email it"
result = await agent.execute_workflow(goal)
```

### 2. Data Collection → Spreadsheet

```python
goal = "Find top GitHub repositories and put them in a Google Sheet"
result = await agent.execute_workflow(goal)
```

### 3. Document Processing

```python
# Ingest documents
await agent.ingest_document("https://arxiv.org/pdf/paper.pdf")
await agent.ingest_document("https://example.com/article.html")

# Query knowledge base
response = await agent.process_message(
    "Compare the methodologies in these papers"
)
```

## Features Showcase

### 🧩 Semantic Chunking

```python
# Document: "Python is popular... [500 words] ...Rust is fast... [500 words]"

# Traditional chunking (fixed 500 words):
# Chunk 1: "Python is popular... ...Rust is fa"  ❌ Cuts mid-sentence

# Our second-topic chunking:
# Chunk 1: "Python is popular..." ✅ Clean topic boundary
# Chunk 2: "Rust is fast..." ✅ Complete topic
```

### 🎯 Multi-Step Planning

```python
# Input: "Find F1 standings, create sheet, email me"

# Agent automatically plans:
step1: extract_webpage
  ↓
step2: google_sheets_upsert (uses step1 data)
  ↓
step3: google_drive_share (uses step2 sheet ID)
  ↓ parallel ↓
step4: screenshot_url → step5: gmail_send (combines 3+4)
```

### 🔍 Semantic Memory

```python
# Ingest documents
agent.ingest_document("article1.pdf")
agent.ingest_document("article2.html")

# Later, ask questions
response = await agent.process_message(
    "What are the common themes?"
)
# Agent retrieves relevant segments from FAISS automatically
```

## Troubleshooting

### Issue: Import errors

```bash
# Reinstall
pip install -e .
```

### Issue: Google OAuth popup doesn't appear

```bash
# Delete cached tokens
rm ~/.config/cursor-agent/google/*_token.json
# Run again
```

### Issue: Screenshot fails

```bash
# Reinstall Playwright
playwright install chromium
```

### Issue: FAISS errors

```bash
# Use CPU version
pip install faiss-cpu --force-reinstall
```

## Documentation

- 📘 [Complete README](README.md) - Full feature list
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md) - Deep dive
- 🛠️ [Setup Guide](docs/SETUP_GUIDE.md) - Detailed setup
- 🏎️ [F1 Workflow](docs/F1_WORKFLOW.md) - Example walkthrough

## Examples

### Example 1: Simple Task

```python
agent = CursorAgent()
response = await agent.process_message(
    "Find the weather forecast and email it to me"
)
print(response)
```

### Example 2: Multi-Document Analysis

```python
# Ingest multiple sources
for url in research_urls:
    await agent.ingest_document(url)

# Analyze
response = await agent.process_message(
    "Compare the conclusions across these papers"
)
```

### Example 3: Custom Workflow

```python
result = await agent.execute_workflow(
    """
    1. Find trending GitHub repos in Python
    2. Create a Google Sheet with name, stars, description
    3. Share it publicly
    4. Send me the link on Telegram
    """
)

print(result["blackboard"]["sheet_url"])
```

## Performance

- **Planning**: 1-3 seconds (Gemini API)
- **FAISS Search**: <50ms (10k vectors)
- **Tool Execution**: 0.5-5s per tool
- **End-to-End**: ~10-30s for typical workflows

## Limitations

- **Mock Mode**: Default runs with mock Google APIs (for quick testing)
- **FAISS Scale**: Single-machine limit ~1M vectors
- **Rate Limits**: Respect API rate limits (Google, Gemini)
- **Sequential Planning**: One plan at a time (no multi-agent yet)

## Community

- 🐛 **Issues**: Report bugs via GitHub Issues
- 💡 **Ideas**: Share feature requests
- 🤝 **Contribute**: PRs welcome!

## License

MIT License - see [LICENSE](LICENSE)

---

**Ready to build?** Start with `python main.py interactive` and explore! 🚀

For production deployment, complete the [Setup Guide](docs/SETUP_GUIDE.md).

