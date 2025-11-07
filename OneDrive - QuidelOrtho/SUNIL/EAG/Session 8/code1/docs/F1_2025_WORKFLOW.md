# F1 2025 Driver Standings Workflow

## Overview

This document explains how the Telegram bot scrapes the 2025 F1 Driver Standings from the official Formula1.com website using Trafilatura and creates a Google Sheet with the data.

---

## Workflow Steps

### 1. **User Triggers Workflow**
Send a message to the Telegram bot containing keywords like:
- "F1"
- "standings" 
- "drivers"
- Or the trigger phrase: "f1"

Example messages:
```
f1
Get F1 standings
Show me the F1 driver standings
```

### 2. **Web Scraping with Trafilatura**

**Source URL**: `https://www.formula1.com/en/results/2025/drivers`

The system uses the **Trafilatura MCP Server** (`trafilatura_sse.py`) to:
- Fetch the HTML content from Formula1.com
- Extract the main content using Trafilatura's intelligent extraction
- Parse the driver standings table
- Convert to structured data (Markdown → Table → Rows)

**Data Extracted**:
- **Position**: Driver ranking (1-21)
- **Driver**: Full name with abbreviation (e.g., "Lando Norris NOR")
- **Nationality**: 3-letter country code (e.g., "GBR", "AUS")
- **Team**: Constructor name (e.g., "McLaren", "Red Bull Racing")
- **Points**: Championship points (e.g., 357, 356)

### 3. **Google Sheets Creation**

The extracted data is uploaded to Google Sheets using the **Google Sheets MCP Server** (`google_sheets_sse.py`):

**Sheet Details**:
- **Spreadsheet Title**: `F1_2025_Driver_Standings`
- **Sheet Name**: `Drivers_2025`
- **Columns**: Position | Driver | Nationality | Team | Points

**Sample Data** (as of latest scrape):
```
Position | Driver              | Nationality | Team                | Points
---------|---------------------|-------------|---------------------|-------
1        | Lando Norris NOR    | GBR         | McLaren            | 357
2        | Oscar Piastri PIA   | AUS         | McLaren            | 356
3        | Max Verstappen VER  | NED         | Red Bull Racing    | 321
4        | George Russell RUS  | GBR         | Mercedes           | 258
5        | Charles Leclerc LEC | MON         | Ferrari            | 210
```

### 4. **File Sharing**

The Google Sheet is shared using the **Google Drive MCP Server** (`google_drive_sse.py`):
- **Sharing Type**: Public (anyone with link)
- **Permission**: Reader
- **Result**: Shareable link generated

### 5. **Email Notification**

An email is sent using the **Gmail MCP Server** (`gmail_sse.py`):
- **To**: Your email (from `SELF_EMAIL` environment variable)
- **Subject**: "F1 Standings Sheet"
- **Content**: Link to the Google Sheet

### 6. **Telegram Response**

The bot sends a reply with:
```
✅ Done. Sheet: [Google Sheets URL]
```

---

## Technical Architecture

### MCP Servers Involved

1. **Trafilatura SSE Server** (Port 8001)
   - Tool: `extract_webpage`
   - Function: Web scraping and content extraction
   - Input: URL (`https://www.formula1.com/en/results/2025/drivers`)
   - Output: Markdown content with table data

2. **Google Sheets SSE Server** (Port 8004)
   - Tool: `google_sheets_upsert`
   - Function: Create/update spreadsheet
   - Input: Title, sheet name, rows (2D array)
   - Output: Spreadsheet ID, URL

3. **Google Drive SSE Server** (Port 8005)
   - Tool: `google_drive_share`
   - Function: Generate shareable link
   - Input: File ID, permissions
   - Output: Public link

4. **Gmail SSE Server** (Port 8006)
   - Tool: `gmail_send`
   - Function: Send email notification
   - Input: Recipient, subject, HTML body
   - Output: Message ID

### Agent Components

```
┌─────────────────┐
│ Telegram Bot    │ ← User sends "f1"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent           │
│ Orchestrator    │ ← Workflow coordination
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Task Planner    │ ← Creates 4-step plan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tool Executor   │ ← Executes each step via SSE
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         MCP SSE Servers                 │
│  ┌──────────┐  ┌──────────┐            │
│  │Trafilatura│  │ Sheets   │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │  Drive   │  │  Gmail   │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```env
# Required: Your email for receiving the sheet link
SELF_EMAIL=your_email@example.com

# Optional: Override default F1 URL
F1_STANDINGS_URL=https://www.formula1.com/en/results/2025/drivers

# Google API Credentials (required)
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json

# Telegram Bot (required)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# SSE Mode (recommended)
USE_SSE_MCP=true
MCP_TRAFILATURA_URL=http://localhost:8001
MCP_SHEETS_URL=http://localhost:8004
MCP_DRIVE_URL=http://localhost:8005
MCP_GMAIL_URL=http://localhost:8006
```

---

## How Trafilatura Works

### Web Scraping Process

1. **HTTP Request**: Fetches HTML from Formula1.com
2. **Content Extraction**: Uses Trafilatura's ML-based extraction
   - Identifies main content area
   - Removes navigation, ads, footers
   - Preserves tables and structured data
3. **Markdown Conversion**: Converts HTML to clean Markdown
4. **Table Parsing**: Extracts table rows and columns
5. **Data Structuring**: Creates 2D array for Google Sheets

### Why Trafilatura?

- ✅ **Intelligent**: Uses ML to identify main content
- ✅ **Robust**: Handles complex HTML structures
- ✅ **Fast**: Optimized for speed
- ✅ **Reliable**: Works across different website layouts
- ✅ **Clean Output**: Returns well-formatted Markdown

### Example Extraction

**Input HTML** (from Formula1.com):
```html
<table class="resultsarchive-table">
  <tr>
    <td>1</td>
    <td>Lando Norris</td>
    <td>GBR</td>
    <td>McLaren</td>
    <td>357</td>
  </tr>
  ...
</table>
```

**Trafilatura Output** (Markdown):
```markdown
| Pos. | Driver | Nationality | Team | Pts. |
|------|--------|-------------|------|------|
| 1    | Lando Norris NOR | GBR | McLaren | 357 |
| 2    | Oscar Piastri PIA | AUS | McLaren | 356 |
...
```

**Parsed Output** (for Google Sheets):
```python
[
    ["Pos.", "Driver", "Nationality", "Team", "Pts."],
    ["1", "Lando Norris NOR", "GBR", "McLaren", "357"],
    ["2", "Oscar Piastri PIA", "AUS", "McLaren", "356"],
    ...
]
```

---

## Error Handling

### Common Issues & Solutions

**1. Web Scraping Fails**
```
❌ Failed at: Extract 2025 F1 driver standings from web
Error: HTTP 403 or timeout
```
**Solution**: 
- Check internet connection
- Verify URL is accessible: https://www.formula1.com/en/results/2025/drivers
- Ensure Trafilatura SSE server is running (port 8001)

**2. Google Sheets API Error**
```
❌ Failed at: Create/update Google Sheet
Error: Google Sheets API not enabled
```
**Solution**:
- Enable Google Sheets API in Google Cloud Console
- See: `ENABLE_GOOGLE_APIS.md`

**3. Email Sending Fails**
```
❌ Failed at: Email sheet link
Error: SELF_EMAIL not configured
```
**Solution**:
- Add `SELF_EMAIL` to your `.env` file
- Ensure Gmail API is enabled

---

## Running the Workflow

### Prerequisites

1. ✅ All 7 SSE servers running
2. ✅ Google APIs enabled (Sheets, Drive, Gmail)
3. ✅ Credentials configured (`credentials.json`)
4. ✅ Environment variables set (`.env`)
5. ✅ Telegram bot configured

### Start Services

```powershell
# Terminal 1: Start SSE servers
python start_sse_servers.py

# Terminal 2: Start Telegram bot
python .cursor\telegram_poller.py
```

### Send Test Message

Open Telegram and send:
```
f1
```

### Expected Output

```
✅ Done. Sheet: https://docs.google.com/spreadsheets/d/[ID]/edit
```

---

## Advanced Usage

### Custom URL

To scrape a different season or page:

```env
# In .env file
F1_STANDINGS_URL=https://www.formula1.com/en/results/2024/drivers
```

### Manual Workflow Trigger

```python
from agent.orchestrator import CursorAgent
import asyncio

async def run():
    agent = CursorAgent()
    result = await agent.execute_workflow(
        "Extract F1 2025 driver standings from "
        "https://www.formula1.com/en/results/2025/drivers "
        "and create a Google Sheet"
    )
    print(result)

asyncio.run(run())
```

### API Mode (without Telegram)

```bash
# Run the main agent
python main.py
```

---

## Monitoring

### Check SSE Server Health

```powershell
# Test Trafilatura server
Invoke-WebRequest -Uri "http://localhost:8001/health"

# Test all servers
$ports = 8001,8004,8005,8006
foreach ($port in $ports) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -TimeoutSec 2
        Write-Host "✅ Port $port OK"
    } catch {
        Write-Host "❌ Port $port FAILED"
    }
}
```

### View Logs

```powershell
# Telegram bot logs
Get-Content telegram_poller.log -Tail 50 -Wait

# SSE server logs (if configured)
Get-Content sse_servers.log -Tail 50 -Wait
```

---

## Data Format

### Current 2025 Season Standings

Based on the latest scrape from Formula1.com:

| Position | Driver | Team | Points |
|----------|--------|------|--------|
| 1 | Lando Norris | McLaren | 357 |
| 2 | Oscar Piastri | McLaren | 356 |
| 3 | Max Verstappen | Red Bull Racing | 321 |
| 4 | George Russell | Mercedes | 258 |
| 5 | Charles Leclerc | Ferrari | 210 |

**Full standings** with all 21 drivers are automatically scraped and uploaded to your Google Sheet.

---

## Troubleshooting

### Workflow Debugging

Enable debug mode in `.cursor/telegram_poller.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components

```powershell
# Test web scraping
curl http://localhost:8001/mcp/tools/call -Method POST -Body '{"name":"extract_webpage","arguments":{"url":"https://www.formula1.com/en/results/2025/drivers"}}' -ContentType "application/json"

# Test Google Sheets
curl http://localhost:8004/mcp/tools/call -Method POST -Body '{"name":"google_sheets_upsert","arguments":{"spreadsheet_title":"Test","sheet_name":"Sheet1","rows":[["A","B"],["1","2"]]}}' -ContentType "application/json"
```

---

## References

- **Formula1.com Official Results**: https://www.formula1.com/en/results/2025/drivers
- **Trafilatura Documentation**: https://trafilatura.readthedocs.io/
- **Google Sheets API**: https://developers.google.com/sheets/api
- **Project Documentation**: `README.md`, `ARCHITECTURE.md`

---

**Last Updated**: November 7, 2025  
**F1 Season**: 2025 (21 drivers, 23 races planned)

