# F1 Standings Workflow - Complete Walkthrough

This document provides a detailed walkthrough of the F1 standings example workflow, demonstrating all four layers of the agent architecture.

## Workflow Overview

**Goal**: Find current F1 driver standings, create a Google Sheet, share it, capture a screenshot, and email it.

**Input**: Single natural language command
**Output**: Google Sheet URL, screenshot file, email confirmation

## Execution Flow

### 1. User Input (Agent Shell)

```python
goal = """Find the Current Point Standings of F1 Racers, 
then put that into a Google Excel Sheet, and then share 
the link to this sheet with yourself on Gmail, and share 
the screenshot"""
```

The agent orchestrator receives this goal and initializes the conversation state:

```python
state = AgentState(
    conversation_id="f1-workflow-001",
    current_goal=goal,
    working_memory=WorkingMemory(...),
    status="processing"
)
```

---

### 2. Decision Layer: Planning

The `TaskPlanner` analyzes the goal and breaks it into steps:

```json
[
  {
    "step_id": "step1",
    "tool": "extract_webpage",
    "args": {"url": "{env.F1_STANDINGS_URL}"},
    "depends_on": [],
    "description": "Fetch F1 driver standings from web"
  },
  {
    "step_id": "step2",
    "tool": "google_sheets_upsert",
    "args": {
      "spreadsheet_title": "F1_Current_Standings",
      "sheet_name": "Drivers",
      "rows": "{step1.rows}"
    },
    "depends_on": ["step1"],
    "description": "Create Google Sheet with standings"
  },
  {
    "step_id": "step3",
    "tool": "google_drive_share",
    "args": {
      "file_id": "{step2.spreadsheet_id}",
      "role": "reader",
      "type": "anyone"
    },
    "depends_on": ["step2"],
    "description": "Share sheet publicly"
  },
  {
    "step_id": "step4",
    "tool": "screenshot_url",
    "args": {"url": "{step2.sheet_url}"},
    "depends_on": ["step2"],
    "description": "Capture screenshot of sheet"
  },
  {
    "step_id": "step5",
    "tool": "gmail_send",
    "args": {
      "to": "{env.SELF_EMAIL}",
      "subject": "F1 Standings Sheet",
      "html": "F1 standings: {step3.link}",
      "attachments": ["{step4.path}"]
    },
    "depends_on": ["step3", "step4"],
    "description": "Email sheet link with screenshot"
  },
  {
    "step_id": "step6",
    "tool": "telegram_send",
    "args": {
      "chat_id": "{env.TELEGRAM_CHAT_ID}",
      "text": "F1 standings sent to email"
    },
    "depends_on": ["step5"],
    "description": "Send confirmation to Telegram"
  }
]
```

**Key Observations:**
- Steps 3 and 4 can run in parallel (both depend only on step2)
- Placeholder references like `{step1.rows}` will be resolved
- Environment variables like `{env.SELF_EMAIL}` are injected

---

### 3. Action Layer: Execution

#### Step 1: Extract F1 Standings

**Tool**: `extract_webpage` via Trafilatura MCP server

**Execution**:
```python
# ToolSelector resolves placeholders
args = {
    "url": "https://www.formula1.com/en/results.html/2025/drivers.html"
}

# ToolExecutor calls MCP server
result = await executor._extract_webpage(args)
```

**Perception Layer Integration**:
```python
# Inside _extract_webpage
ingestion = DocumentIngestion()
doc, markdown = ingestion.ingest_document(url, SourceKind.HTML)

# Parse markdown table
rows = [
    ["Position", "Driver", "Team", "Points"],
    ["1", "Max Verstappen", "Red Bull Racing", "575"],
    ["2", "Sergio Perez", "Red Bull Racing", "285"],
    ...
]
```

**Output**:
```json
{
  "markdown": "# F1 Driver Standings...",
  "doc_id": "a1b2c3d4e5f6",
  "rows": [["Position", "Driver", "Team", "Points"], ...]
}
```

**Blackboard Update**:
```python
blackboard["extracted_content"] = markdown
blackboard["data_rows"] = rows
blackboard["step_step1"] = result
```

---

#### Step 2: Create Google Sheet

**Tool**: `google_sheets_upsert` via Google Sheets MCP server

**Execution**:
```python
# Resolved args (placeholders replaced)
args = {
    "spreadsheet_title": "F1_Current_Standings",
    "sheet_name": "Drivers",
    "rows": [
        ["Position", "Driver", "Team", "Points"],
        ["1", "Max Verstappen", "Red Bull Racing", "575"],
        ...
    ]
}

# Call MCP server
result = await executor._google_sheets_upsert(args)
```

**MCP Server Implementation**:
```python
# In google_sheets_stdio.py
creds = self._get_credentials()  # OAuth flow
service = build('sheets', 'v4', credentials=creds)

# Create spreadsheet
spreadsheet = service.spreadsheets().create(
    body={'properties': {'title': 'F1_Current_Standings'}}
).execute()

# Insert data
service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range="Drivers!A1",
    body={'values': rows}
).execute()
```

**Output**:
```json
{
  "spreadsheet_id": "1abc...xyz",
  "sheet_url": "https://docs.google.com/spreadsheets/d/1abc...xyz",
  "rows_inserted": 21
}
```

**Blackboard Update**:
```python
blackboard["spreadsheet_id"] = "1abc...xyz"
blackboard["sheet_url"] = "https://docs.google.com/..."
```

---

#### Steps 3 & 4: Parallel Execution

Since steps 3 and 4 both depend only on step2, they execute in parallel:

**Step 3: Share Drive File**
```python
args = {
    "file_id": "1abc...xyz",  # From step2
    "role": "reader",
    "type": "anyone"
}
result = await executor._google_drive_share(args)
# Output: {"link": "https://...", "permission_id": "..."}
```

**Step 4: Capture Screenshot**
```python
args = {
    "url": "https://docs.google.com/spreadsheets/d/1abc...xyz"
}
result = await executor._screenshot_url(args)
# Output: {"path": "./data/screenshots/screenshot_123.png"}
```

Both execute simultaneously, improving latency.

---

#### Step 5: Send Email

**Tool**: `gmail_send` via Gmail MCP server

**Execution**:
```python
args = {
    "to": "user@example.com",
    "subject": "F1 Standings Sheet",
    "html": "F1 standings: https://docs.google.com/...",
    "attachments": ["./data/screenshots/screenshot_123.png"]
}

result = await executor._gmail_send(args)
```

**MCP Server Implementation**:
```python
# Create MIME message
message = MIMEMultipart()
message['to'] = to
message['subject'] = subject
message.attach(MIMEText(html, 'html'))

# Attach screenshot
with open(screenshot_path, 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    message.attach(part)

# Send via Gmail API
service.users().messages().send(
    userId='me',
    body={'raw': base64.urlsafe_b64encode(message.as_bytes())}
).execute()
```

**Output**:
```json
{
  "message_id": "abc123xyz",
  "to": "user@example.com",
  "subject": "F1 Standings Sheet"
}
```

---

#### Step 6: Telegram Confirmation

**Tool**: `telegram_send` via Telegram MCP server

**Execution**:
```python
args = {
    "chat_id": "123456789",
    "text": "✅ F1 standings sent to email"
}

result = await executor._telegram_send(args)
```

**Output**:
```json
{
  "ok": true,
  "chat_id": "123456789",
  "message_id": 987654
}
```

---

### 4. Memory Layer: Persistence

Throughout execution, the agent logs to memory:

**Working Memory** (Short-term):
```python
working_memory.add_message(MemoryEntry(
    entry_id="msg001",
    conversation_id="f1-workflow-001",
    content="User: Find F1 standings...",
    entry_type="user_message"
))

working_memory.set_blackboard_value("sheet_url", sheet_url)
working_memory.set_blackboard_value("screenshot_path", path)
```

**Scratchpad** (Long-term JSONL):
```jsonl
{"entry_id":"msg001","conversation_id":"f1-workflow-001","content":"User: Find F1 standings...","entry_type":"user_message","timestamp":"2025-11-02T10:30:00"}
{"entry_id":"tool001","conversation_id":"f1-workflow-001","content":"Executed extract_webpage → 21 rows","entry_type":"tool_result","timestamp":"2025-11-02T10:30:15"}
{"entry_id":"tool002","conversation_id":"f1-workflow-001","content":"Created Google Sheet: 1abc...xyz","entry_type":"tool_result","timestamp":"2025-11-02T10:30:30"}
```

**FAISS Vector Store**:
```python
# If we ingest the F1 standings page
doc, markdown = ingestion.ingest_document(f1_url)
segments = chunker.chunk_document(doc, markdown)
embeddings = embedder.embed_segments(segments)
vector_store.add_embeddings(embeddings, segments)
```

Now future queries like "What was Max Verstappen's points?" can retrieve from vector store.

---

### 5. Response Generation

After successful execution:

```python
response = agent._generate_success_response(plan, blackboard)
```

**Output**:
```
✓ Successfully completed: Find the Current Point Standings...

📊 Google Sheet: https://docs.google.com/spreadsheets/d/1abc...xyz
🔗 Share link: https://docs.google.com/spreadsheets/d/1abc...xyz/edit?usp=sharing
📸 Screenshot saved: ./data/screenshots/screenshot_123.png
📧 Email sent (ID: abc123xyz)

Completed 6/6 steps.
```

---

## Data Flow Diagram

```
User Input
    │
    ▼
[Decision] Planning
    │
    ▼
[Action] Step 1: extract_webpage
    │ → [Perception] Trafilatura → Markdown
    │ → [Perception] Parse table → rows
    ▼
[Memory] Blackboard ← rows
    │
    ▼
[Action] Step 2: google_sheets_upsert
    │ → [Action] Google Sheets API
    ▼
[Memory] Blackboard ← spreadsheet_id, sheet_url
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Step 3: share     Step 4: screenshot  [parallel]
    │                  │
    ▼                  ▼
[Memory] ← link    [Memory] ← path
    │                  │
    └──────────────────┴──────────────────┐
                                          ▼
                            [Action] Step 5: gmail_send
                                          │
                                          ▼
                            [Action] Step 6: telegram_send
                                          │
                                          ▼
                                     Response to User
```

---

## Key Architectural Features Demonstrated

### 1. Separation of Concerns
- **Perception** handles all document processing
- **Memory** manages state persistence
- **Decision** plans execution strategy
- **Action** executes tools

### 2. Dependency Management
- Steps 3 & 4 run in parallel (both depend on step2)
- Step 5 waits for both 3 & 4 (attachment + link)
- Automatic topological sort of dependencies

### 3. Placeholder Resolution
```python
"{step2.sheet_url}" → "https://docs.google.com/..."
"{env.SELF_EMAIL}" → "user@example.com"
"{step1.rows}" → [["Position", "Driver", ...]]
```

### 4. Blackboard Pattern
- Shared state across all tools
- Semantic keys: `sheet_url`, `screenshot_path`
- Step-specific keys: `step_step2`, `step_step3`

### 5. Error Handling
```python
if not result.success:
    plan.status = "failed"
    return False, blackboard
```

### 6. Observability
```python
print(f"[MOCK] Created Google Sheet: {title}")
print(f"[MOCK] Sheet URL: {sheet_url}")
```

---

## Running the Workflow

### Command Line
```bash
python main.py f1
```

### Python API
```python
from agent.orchestrator import CursorAgent
import asyncio

async def main():
    agent = CursorAgent()
    result = await agent.execute_workflow(
        "Find F1 standings and email them to me"
    )
    print(result["blackboard"]["sheet_url"])

asyncio.run(main())
```

### Expected Output
```
============================================================
Cursor Agent - F1 Standings Workflow
============================================================

🎯 Goal: Find the Current Point Standings of F1 Racers...

[MOCK] Created Google Sheet: F1_Current_Standings
[MOCK] Sheet URL: https://docs.google.com/spreadsheets/d/mock_...
[MOCK] Shared file mock_... with anyone as reader
[MOCK] Captured screenshot of https://docs.google.com/...
[MOCK] Sent email to user@example.com
[MOCK] Sent Telegram message to 123456789

============================================================
RESULTS
============================================================
✅ Workflow completed successfully!

📋 Plan: 6 steps
  ✓ 1. Fetch F1 driver standings from web
  ✓ 2. Create Google Sheet with standings
  ✓ 3. Share sheet publicly
  ✓ 4. Capture screenshot of sheet
  ✓ 5. Email sheet link with screenshot
  ✓ 6. Send confirmation to Telegram

📊 Outputs:
  - spreadsheet_id: mock_f1_current_standings
  - sheet_url: https://docs.google.com/spreadsheets/d/mock_...
  - share_link: https://docs.google.com/spreadsheets/d/mock_...
  - screenshot_path: ./data/screenshots/screenshot_....png
  - email_message_id: mock_msg_...

✓ Saved agent state

============================================================
```

---

## Customization

### Change Data Source
```python
# In .env
F1_STANDINGS_URL=https://your-custom-f1-source.com/standings
```

### Use Pre-configured Output Sheet
```python
# In .env - Specify an existing Google Sheet for output
F1_OUTPUT_SHEET_URL=https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY/edit?usp=drive_link
F1_OUTPUT_SHEET_ID=1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY

# Note: This is optional. If not set, the agent will create a new sheet each time.
```

### Add More Steps
```python
# In the planner, add:
{
    "step_id": "step7",
    "tool": "slack_send",
    "args": {"channel": "#f1", "text": "New standings posted!"},
    "depends_on": ["step5"]
}
```

### Modify Sheet Format
```python
# In executor, transform rows:
rows = [
    ["Position", "Driver", "Points"],  # Simplified columns
    *[[r[0], r[1], r[3]] for r in raw_rows[1:]]
]
```

---

## Troubleshooting

### Empty Standings Table
- Check F1_STANDINGS_URL is correct
- Verify Trafilatura can parse the page
- Inspect `blackboard["extracted_content"]`

### Google OAuth Errors
- Delete `~/.config/cursor-agent/google/*_token.json`
- Rerun to get fresh OAuth prompt
- Check APIs are enabled in Google Cloud Console

### Screenshot Timeout
- Increase Playwright timeout: `page.set_default_timeout(30000)`
- Check sheet URL is accessible
- Verify Chromium is installed: `playwright install chromium`

---

## Next Steps

1. **Add Semantic Search**: Store standings in FAISS, query "Who leads in points?"
2. **Scheduled Execution**: Run workflow weekly with cron
3. **Real-time Updates**: Use SSE MCP server for streaming progress
4. **Multi-format Export**: Add PDF/CSV export tools
5. **Comparative Analysis**: Track changes over time

---

**Happy Racing! 🏎️**

