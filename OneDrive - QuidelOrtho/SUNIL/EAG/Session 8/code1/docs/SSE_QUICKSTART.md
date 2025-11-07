# SSE MCP Servers - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you quickly set up and run the SSE-based MCP servers.

## Prerequisites

- Python 3.8+
- All dependencies installed (`pip install -r requirements.txt` or `uv sync`)
- Google API credentials configured (if using Google services)

## Step 1: Configure Environment

Copy the example environment file:
```bash
cp env.example .env
```

Edit `.env` and ensure SSE is enabled:
```bash
# Enable SSE MCP servers
USE_SSE_MCP=true

# Add your credentials
TELEGRAM_BOT_TOKEN=your_token_here
SELF_EMAIL=your_email@example.com
```

## Step 2: Start SSE Servers

Run the startup script:
```bash
python start_sse_servers.py
```

You should see:
```
============================================================
🚀 Starting SSE MCP Servers
============================================================

[Trafilatura] Starting on port 8001...
[Trafilatura] ✅ Running on http://localhost:8001

[MuPDF4LLM] Starting on port 8002...
[MuPDF4LLM] ✅ Running on http://localhost:8002

...

============================================================
✅ All servers started
============================================================

Server Status:
  • Trafilatura         http://localhost:8001
  • MuPDF4LLM           http://localhost:8002
  • Gemma Caption       http://localhost:8003
  • Google Sheets       http://localhost:8004
  • Google Drive        http://localhost:8005
  • Gmail               http://localhost:8006
  • Telegram            http://localhost:8007
  • Screenshot          http://localhost:8008

Press Ctrl+C to stop all servers
============================================================
```

## Step 3: Test the Servers

### Test Individual Server

```bash
# Test trafilatura server
curl http://localhost:8001/health

# Should return: {"status": "ok", "server": "trafilatura-sse"}
```

### Test Tool Call

```bash
curl -X POST http://localhost:8001/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "fetch_markdown", "arguments": {"url": "https://example.com"}}'
```

### List Available Tools

```bash
curl http://localhost:8001/mcp/tools/list
```

## Step 4: Run the Agent

In a **new terminal** (keep servers running):

```bash
# Run the F1 workflow
python main.py f1

# Or start interactive chat
python main.py interactive
```

The agent will automatically use the SSE servers!

## Step 5: Run Telegram Bot

In a **new terminal**:

```bash
python .cursor/telegram_poller.py
```

Send a message to your bot:
```
Get F1 standings and create a sheet
```

## Verification Checklist

✅ All 8 servers show green checkmarks  
✅ Health checks return {"status": "ok"}  
✅ Agent runs without errors  
✅ Telegram bot responds to messages  

## Troubleshooting

### Problem: Port already in use

**Error:**
```
[Trafilatura] ❌ Failed to start: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process using the port
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux/Mac

# Kill the process
taskkill /PID <pid> /F        # Windows
kill -9 <pid>                 # Linux/Mac
```

### Problem: Health check fails

**Error:**
```
[Trafilatura] ⚠️  Started but health check failed
```

**Solution:**
1. Wait a few more seconds for server to fully start
2. Check server logs for errors
3. Try restarting: Ctrl+C then run `start_sse_servers.py` again

### Problem: SSE connection errors in agent

**Error:**
```
[WARN] SSE call failed, falling back to direct call: Connection refused
```

**Solution:**
1. Ensure SSE servers are running (`python start_sse_servers.py`)
2. Check `.env` has `USE_SSE_MCP=true`
3. Verify server URLs are correct in `.env`

## Common Commands

### Start Servers
```bash
python start_sse_servers.py
```

### Stop Servers
Press `Ctrl+C` in the terminal running the servers

### Start Individual Server
```bash
python -m mcp_servers.trafilatura_sse --port 8001
```

### Check All Server Health
```bash
for port in 8001 8002 8003 8004 8005 8006 8007 8008; do
  echo "Checking port $port:"
  curl -s http://localhost:$port/health
  echo ""
done
```

### Run Agent with SSE
```bash
# Set environment and run
export USE_SSE_MCP=true  # Linux/Mac
set USE_SSE_MCP=true     # Windows CMD
$env:USE_SSE_MCP="true"  # Windows PowerShell

python main.py f1
```

### Run Agent without SSE (Direct Calls)
```bash
export USE_SSE_MCP=false  # Linux/Mac
set USE_SSE_MCP=false     # Windows CMD
$env:USE_SSE_MCP="false"  # Windows PowerShell

python main.py f1
```

## Architecture Overview

```
Your Application (Agent/Bot)
           ↓
    SSE Client Pool
           ↓
    ┌──────┴──────┐
    ▼             ▼
Server :8001  Server :8004  ... (8 servers total)
```

## Next Steps

- 📖 Read [SSE_ARCHITECTURE.md](./SSE_ARCHITECTURE.md) for detailed architecture
- 🔧 Customize server configurations in `.env`
- 🚀 Deploy servers to production (see [SSE_ARCHITECTURE.md](./SSE_ARCHITECTURE.md#docker-deployment))
- 📊 Add monitoring and logging

## Key Features

✅ **Independent Services** - Each tool runs as separate HTTP server  
✅ **Automatic Fallback** - Falls back to direct calls if SSE unavailable  
✅ **Easy Monitoring** - Health checks and individual server logs  
✅ **Scalable** - Deploy and scale each service independently  
✅ **Remote Ready** - Can access servers over network  

## Support

For more information:
- Full architecture: [SSE_ARCHITECTURE.md](./SSE_ARCHITECTURE.md)
- Setup guide: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- F1 workflow: [F1_WORKFLOW.md](./F1_WORKFLOW.md)

## Summary

You now have:
- ✅ 8 independent SSE MCP servers running
- ✅ Agent configured to use SSE servers
- ✅ Automatic fallback if servers unavailable
- ✅ Production-ready architecture

Enjoy your scalable, distributed MCP infrastructure! 🎉

