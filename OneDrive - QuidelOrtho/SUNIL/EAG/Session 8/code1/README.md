# Cursor Agent with Perception-Memory-Decision-Action Architecture

A sophisticated multi-layer agent system for Cursor that implements a complete Perception-Memory-Decision-Action architecture with MCP integrations, semantic chunking, and FAISS-powered memory.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        AGENT SHELL                          │
│  (Orchestration, Conversation Loop, State Management)       │
└─────────────────────────────────────────────────────────────┘
              │                    │                    │
    ┌─────────▼─────────┐  ┌──────▼──────┐  ┌─────────▼─────────┐
    │   PERCEPTION      │  │   MEMORY    │  │    DECISION       │
    │                   │  │             │  │                   │
    │ • Ingestion       │  │ • FAISS     │  │ • Planner         │
    │ • Chunking        │  │ • Scratchpad│  │ • Tool Selector   │
    │ • Embeddings      │  │ • Working   │  │                   │
    └─────────┬─────────┘  └──────┬──────┘  └─────────┬─────────┘
              │                   │                    │
              └───────────────────┴────────────────────┘
                                  │
                          ┌───────▼───────┐
                          │    ACTION     │
                          │               │
                          │ • MCP Tools   │
                          │ • Execution   │
                          └───────────────┘
```

### Four Layers

1. **Perception Layer**: Document ingestion, conversion, semantic chunking, and embedding generation
   - Trafilatura for web pages → Markdown
   - MuPDF4LLM for PDFs → Markdown + images
   - Gemma for image captioning → alt-text
   - Semantic chunking with "second-topic rule" (512-word blocks)
   - Nomic embeddings (L2-normalized)

2. **Memory Layer**: Vector storage and context management
   - FAISS vector store for semantic search
   - Long-term scratchpad (JSONL)
   - Short-term working memory (rolling window)
   - Blackboard for inter-tool state sharing

3. **Decision Layer**: Planning and tool orchestration
   - Multi-step task planning with dependency graphs
   - Tool selection and argument resolution
   - Placeholder resolution from blackboard/previous steps

4. **Action Layer**: Tool execution via MCP
   - MCP stdio servers for all integrations
   - Parallel execution of independent steps
   - Automatic blackboard updates with semantic keys

## Features

- ✅ **Semantic Chunking**: "Second-topic rule" - automatically detects topic boundaries
- ✅ **FAISS Vector Store**: L2-normalized Nomic embeddings for semantic search
- ✅ **Multi-step Planning**: Dependency-aware execution with automatic parallelization
- ✅ **MCP Integrations**: stdio servers for 8+ tools (Google, Telegram, web extraction)
- ✅ **Memory Management**: Working memory + scratchpad + vector store
- ✅ **Pydantic Models**: Type-safe data contracts across all layers
- ✅ **Google Workspace**: Sheets, Drive, Gmail integration
- ✅ **Telegram Bot**: Send notifications and messages
- ✅ **Screenshot Capture**: Playwright-powered webpage screenshots

## Installation

### Prerequisites

- Python 3.11+
- Google Cloud Project (for Google APIs)
- Telegram Bot Token (optional)
- Gemini API Key (for Gemini models)

### Setup

1. **Clone and install dependencies:**

```bash
cd <your-workspace>
uv pip install -e .
```

2. **Install Playwright (for screenshots):**

```bash
playwright install chromium
```

3. **Set up environment variables:**

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Required variables:
```bash
# Google APIs
GOOGLE_CLIENT_SECRET_PATH=~/.config/cursor-agent/google/client_secret.json
GOOGLE_DRIVE_TOKEN_PATH=~/.config/cursor-agent/google/drive_token.json
GOOGLE_SHEETS_TOKEN_PATH=~/.config/cursor-agent/google/sheets_token.json
GOOGLE_GMAIL_TOKEN_PATH=~/.config/cursor-agent/google/gmail_token.json

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Agent
SELF_EMAIL=your_email@example.com
F1_STANDINGS_URL=https://www.formula1.com/en/results.html/2025/drivers.html

# F1 output Google Sheet (optional - pre-configured output destination)
F1_OUTPUT_SHEET_URL=https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY/edit?usp=drive_link
F1_OUTPUT_SHEET_ID=1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY
```

4. **Set up Google APIs:**

   a. Go to [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project or select existing
   
   c. Enable these APIs:
      - Google Drive API
      - Google Sheets API
      - Gmail API
   
   d. Create OAuth 2.0 credentials (Desktop app)
   
   e. Download `client_secret.json` and save to:
      ```
      ~/.config/cursor-agent/google/client_secret.json
      ```
   
   f. First run will open browser for OAuth consent

5. **Set up Telegram (optional):**

   a. Message [@BotFather](https://t.me/BotFather) on Telegram
   
   b. Create a new bot with `/newbot`
   
   c. Copy the bot token to `.env`
   
   d. Get your chat ID from [@getidsbot](https://t.me/getidsbot)

## Usage

### Run F1 Standings Workflow

The complete end-to-end example:

```bash
python main.py f1
```

This will:
1. 📊 Extract F1 standings from the web
2. 📝 Create a Google Sheet with the data
3. 🔗 Share the sheet publicly
4. 📸 Capture a screenshot
5. 📧 Email you the link with screenshot
6. ✅ Send Telegram confirmation (if configured)

### Interactive Mode

Chat with the agent:

```bash
python main.py interactive
```

Commands:
- Type any message to interact
- `ingest <url>` - Ingest a document into memory
- `memory` - View memory summary
- `exit` - Quit

Example session:
```
👤 You: Find the latest Python news and summarize it

🤖 Agent: Processing...

✓ Successfully completed: Find the latest Python news and summarize it
📊 Found 5 articles
📝 Summary saved to memory

Completed 3/3 steps.
```

### Python API

Use the agent in your own code:

```python
import asyncio
from agent.orchestrator import CursorAgent

async def main():
    agent = CursorAgent()
    
    # Process a message
    response = await agent.process_message(
        "Create a Google Sheet with the top 10 Python packages"
    )
    print(response)
    
    # Ingest a document
    doc_id = await agent.ingest_document(
        "https://example.com/article.html"
    )
    
    # Execute a workflow
    result = await agent.execute_workflow(
        "Summarize the ingested article and email it to me"
    )
    
    # Save state
    agent.save_state()

asyncio.run(main())
```

## MCP Server Configuration

The agent uses MCP stdio servers for all external integrations. Configuration is in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "trafilatura-stdio": {
      "command": "python",
      "args": ["-m", "mcp_servers.trafilatura_stdio"]
    },
    "google-sheets-stdio": {
      "command": "python",
      "args": ["-m", "mcp_servers.google_sheets_stdio"]
    },
    ...
  }
}
```

Each server implements the MCP protocol with:
- `tools/list` - List available tools
- `tools/call` - Execute a tool

## Project Structure

```
cursor-agent/
├── agent/                      # Main agent package
│   ├── models.py              # Pydantic data models
│   ├── orchestrator.py        # Agent orchestration loop
│   ├── perception/            # Perception layer
│   │   ├── ingestion.py       # Document ingestion
│   │   ├── chunking.py        # Semantic chunking
│   │   └── embeddings.py      # Embedding generation
│   ├── memory/                # Memory layer
│   │   ├── vector_store.py    # FAISS vector store
│   │   ├── scratchpad.py      # Long-term memory
│   │   └── working_memory.py  # Short-term memory
│   ├── decision/              # Decision layer
│   │   ├── planner.py         # Task planning
│   │   └── tool_selector.py   # Tool selection
│   └── action/                # Action layer
│       └── executor.py        # Tool execution
├── mcp_servers/               # MCP server implementations
│   ├── trafilatura_stdio.py   # Web extraction
│   ├── mupdf4llm_stdio.py     # PDF extraction
│   ├── gemma_caption_stdio.py # Image captioning
│   ├── google_sheets_stdio.py # Google Sheets
│   ├── google_drive_stdio.py  # Google Drive
│   ├── gmail_stdio.py         # Gmail
│   ├── telegram_stdio.py      # Telegram
│   └── screenshot_stdio.py    # Screenshots
├── .cursor/
│   └── mcp.json               # MCP configuration
├── main.py                    # Entry point
├── pyproject.toml             # Dependencies
└── README.md                  # This file
```

## Semantic Chunking: Second-Topic Rule

The agent uses a novel chunking strategy:

1. Split text into 512-word blocks
2. For each block, ask LLM: "Does this contain TWO topics?"
3. If yes:
   - Finalize the FIRST topic as a segment
   - Prepend the SECOND topic to the next block
4. If no: finalize the entire block
5. Recursively process with carry-over

This ensures segments are semantically coherent and don't break in the middle of topics.

## Memory Architecture

### Three-Tier Memory System

1. **Working Memory** (Short-term)
   - Rolling window of last N messages
   - Blackboard for inter-tool state
   - Fast in-memory access

2. **Scratchpad** (Long-term)
   - JSONL file of all conversations
   - Searchable by conversation ID
   - Persistent across sessions

3. **Vector Store** (Semantic)
   - FAISS index with L2-normalized embeddings
   - Semantic search over all ingested content
   - Metadata filters (doc_id, conversation_id, etc.)

## Tool Catalog

### Available Tools

| Tool | Description | MCP Server |
|------|-------------|------------|
| `extract_webpage` | Fetch webpage → Markdown | trafilatura-stdio |
| `extract_pdf` | PDF → Markdown + images | mupdf4llm-stdio |
| `caption_image` | Generate alt-text | gemma-caption-stdio |
| `google_sheets_upsert` | Create/update Sheet | google-sheets-stdio |
| `google_drive_share` | Share Drive file | google-drive-stdio |
| `gmail_send` | Send email | gmail-stdio |
| `telegram_send` | Send Telegram message | telegram-stdio |
| `screenshot_url` | Capture screenshot | screenshot-stdio |

### Adding New Tools

1. Create MCP stdio server in `mcp_servers/`
2. Add to `.cursor/mcp.json`
3. Add handler in `agent/action/executor.py`
4. Update tool catalog in `agent/decision/planner.py`

## Example Workflows

### 1. F1 Standings → Sheet → Email

```python
goal = """Find the Current Point Standings of F1 Racers, 
put that into a Google Sheet, and email me the link."""

result = await agent.execute_workflow(goal)
```

**Execution Plan:**
```
step1: extract_webpage (F1 standings URL)
  ↓
step2: google_sheets_upsert (create sheet with data)
  ↓
step3: google_drive_share (make publicly viewable)
  ↓
step4: screenshot_url (capture sheet screenshot)
  ↓
step5: gmail_send (email link + screenshot)
  ↓
step6: telegram_send (confirmation message)
```

### 2. Research + Summarize + Share

```python
goal = """Find articles about Rust programming, 
ingest them, create a summary document, 
and share it on Google Drive."""

await agent.execute_workflow(goal)
```

### 3. Document Processing Pipeline

```python
# Ingest multiple documents
for url in urls:
    await agent.ingest_document(url)

# Query the knowledge base
response = await agent.process_message(
    "What are the common themes across these documents?"
)
```

## Troubleshooting

### Google OAuth Issues

If you get credential errors:
1. Delete token files: `~/.config/cursor-agent/google/*_token.json`
2. Run again - browser will open for fresh OAuth
3. Check that all APIs are enabled in Google Cloud Console

### FAISS Installation

If FAISS fails to install:
```bash
# Use CPU-only version
pip install faiss-cpu

# Or for GPU support
pip install faiss-gpu
```

### Playwright Issues

If screenshots fail:
```bash
# Reinstall browsers
playwright install chromium

# Or install dependencies
playwright install-deps
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

Follow the 4-layer architecture:
- **Perception**: Pure functions for ingestion/chunking/embedding
- **Memory**: Stateful storage with clear interfaces
- **Decision**: Stateless planning and tool selection
- **Action**: Async tool execution

### Adding Features

1. Add Pydantic model in `agent/models.py`
2. Implement in appropriate layer
3. Update orchestrator if needed
4. Add tests

## Credits

Built with:
- [Trafilatura](https://trafilatura.readthedocs.io/) - Web content extraction
- [MuPDF4LLM](https://pymupdf.readthedocs.io/) - PDF processing
- [FAISS](https://faiss.ai/) - Vector similarity search
- [Sentence Transformers](https://www.sbert.net/) - Nomic embeddings
- [Google Gemini](https://ai.google.dev/) - Planning and reasoning
- [Playwright](https://playwright.dev/) - Browser automation

## License

MIT License - see LICENSE file for details.

## Next Steps

- [ ] Add SSE event streaming for real-time updates
- [ ] Implement retry logic with exponential backoff
- [ ] Add more MCP servers (Slack, Discord, etc.)
- [ ] Build web UI for agent interaction
- [ ] Add observability (traces, metrics)
- [ ] Support for multi-modal inputs

---

**Questions?** Open an issue or check the [documentation](./docs/).

