# SSE MCP Server Architecture

## Overview

This document describes the SSE (Server-Sent Events) based MCP (Model Context Protocol) server architecture implemented in this project.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Cursor Agent / Telegram Bot            │
│                     (Client Application)                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ HTTP/SSE
                      │
    ┌─────────────────┴─────────────────┐
    │     SSE MCP Client Pool           │
    │  (mcp_servers/sse_client.py)      │
    └─────────────────┬─────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Trafilatura  │ │Google Sheets │ │   Screenshot │
│  SSE Server  │ │  SSE Server  │ │  SSE Server  │
│ Port: 8001   │ │ Port: 8004   │ │ Port: 8008   │
└──────────────┘ └──────────────┘ └──────────────┘

Plus 5 more SSE servers (MuPDF4LLM, Gemma, Drive, Gmail, Telegram)
```

## Components

### 1. SSE Base Server (`mcp_servers/sse_base.py`)

Base class for all SSE MCP servers providing:
- HTTP server infrastructure (using aiohttp)
- Standard MCP protocol endpoints
- SSE connection handling
- Health check endpoints

**Endpoints:**
- `POST /mcp/initialize` - Initialize connection with server
- `GET /mcp/tools/list` - List available tools
- `POST /mcp/tools/call` - Execute a tool
- `GET /mcp/sse` - SSE connection for real-time updates
- `GET /health` - Health check

### 2. SSE MCP Client (`mcp_servers/sse_client.py`)

Client library for agent to communicate with SSE servers:
- `SSEMCPClient` - Single server client
- `SSEMCPClientPool` - Manages multiple server connections
- Automatic retry and error handling
- Connection pooling

### 3. Individual SSE Servers

8 specialized MCP servers, each on its own port:

| Server | Port | Module | Description |
|--------|------|--------|-------------|
| Trafilatura | 8001 | `trafilatura_sse.py` | Web content extraction |
| MuPDF4LLM | 8002 | `mupdf4llm_sse.py` | PDF to Markdown |
| Gemma Caption | 8003 | `gemma_caption_sse.py` | Image captioning |
| Google Sheets | 8004 | `google_sheets_sse.py` | Spreadsheet operations |
| Google Drive | 8005 | `google_drive_sse.py` | File sharing |
| Gmail | 8006 | `gmail_sse.py` | Email sending |
| Telegram | 8007 | `telegram_sse.py` | Telegram messaging |
| Screenshot | 8008 | `screenshot_sse.py` | Screenshot capture |

### 4. Tool Executor (`agent/action/executor.py`)

Updated to support both SSE and direct calls:
- Environment variable `USE_SSE_MCP=true` enables SSE mode
- Automatic fallback to direct calls if SSE fails
- Transparent switching between modes

### 5. Server Manager (`start_sse_servers.py`)

Manages lifecycle of all SSE servers:
- Starts all 8 servers simultaneously
- Health checks for each server
- Monitors server health
- Graceful shutdown on Ctrl+C

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable SSE MCP servers
USE_SSE_MCP=true

# Server URLs (can be customized)
MCP_TRAFILATURA_URL=http://localhost:8001
MCP_MUPDF4LLM_URL=http://localhost:8002
MCP_GEMMA_URL=http://localhost:8003
MCP_SHEETS_URL=http://localhost:8004
MCP_DRIVE_URL=http://localhost:8005
MCP_GMAIL_URL=http://localhost:8006
MCP_TELEGRAM_URL=http://localhost:8007
MCP_SCREENSHOT_URL=http://localhost:8008
```

### MCP Configuration (`.cursor/mcp_sse.json`)

```json
{
  "mcpServers": {
    "trafilatura-sse": {
      "url": "http://localhost:8001",
      "description": "Web content extraction"
    },
    ...
  }
}
```

## Usage

### Starting SSE Servers

**Start all servers:**
```bash
python start_sse_servers.py
```

**Start individual server:**
```bash
# Trafilatura on port 8001
python -m mcp_servers.trafilatura_sse --port 8001

# Google Sheets on port 8004
python -m mcp_servers.google_sheets_sse --port 8004
```

### Using from Agent

The agent automatically uses SSE servers when `USE_SSE_MCP=true`:

```python
from agent.orchestrator import CursorAgent

# Agent will automatically use SSE servers
agent = CursorAgent()

# Execute workflow
result = await agent.execute_workflow(
    "Find F1 standings and create a Google Sheet"
)
```

### Using SSE Client Directly

```python
from mcp_servers.sse_client import SSEMCPClient

async with SSEMCPClient("http://localhost:8001") as client:
    # List tools
    tools = await client.list_tools()
    print(tools)
    
    # Call tool
    result = await client.call_tool(
        tool_name="fetch_markdown",
        arguments={"url": "https://example.com"}
    )
    print(result)
```

### Using Client Pool

```python
from mcp_servers.sse_client import get_client_pool

# Get global client pool
pool = get_client_pool()

# Call tool on specific server
result = await pool.call_tool(
    server_name="trafilatura",
    tool_name="fetch_markdown",
    arguments={"url": "https://example.com"}
)
```

## Benefits of SSE Architecture

### 1. **Scalability**
- Each server runs independently
- Can scale individual services
- Easy to distribute across machines

### 2. **Reliability**
- Server failures don't crash the agent
- Automatic fallback to direct calls
- Individual server restarts without downtime

### 3. **Development**
- Test individual servers in isolation
- Easy to add new tools
- Clear separation of concerns

### 4. **Monitoring**
- Health checks for each server
- Individual server logs
- Easy debugging

### 5. **Deployment**
- Can deploy servers separately
- Remote server support
- Load balancing possible

## Protocol Details

### MCP Tool Call Flow

```
1. Client → POST /mcp/tools/call
   {
     "name": "fetch_markdown",
     "arguments": {"url": "..."}
   }

2. Server executes tool

3. Server → Response
   {
     "content": [{
       "type": "text",
       "text": "{\"markdown\": \"...\", \"images\": [...]}"
     }]
   }
```

### SSE Connection

```
1. Client → GET /mcp/sse

2. Server sends:
   data: {"type": "connected", "server": "trafilatura-sse"}
   
3. Server sends heartbeats every 30s:
   data: {"type": "heartbeat"}
```

## Troubleshooting

### Server Won't Start

**Check port availability:**
```bash
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8001
```

**Kill existing process:**
```bash
# Windows
taskkill /PID <pid> /F

# Linux/Mac
kill -9 <pid>
```

### Connection Errors

**Check server health:**
```bash
curl http://localhost:8001/health
```

**Check logs:**
Each server prints detailed logs to stdout.

### Fallback to Direct Calls

If SSE fails, the agent automatically falls back to direct library calls:
```
[WARN] SSE call failed, falling back to direct call: Connection refused
```

This ensures the agent continues working even if servers are down.

## Migration from stdio

### Old (stdio):
```json
{
  "mcpServers": {
    "trafilatura-stdio": {
      "command": "python",
      "args": ["-m", "mcp_servers.trafilatura_stdio"]
    }
  }
}
```

### New (SSE):
```json
{
  "mcpServers": {
    "trafilatura-sse": {
      "url": "http://localhost:8001"
    }
  }
}
```

### Code Changes:
No code changes needed! The executor automatically uses SSE when enabled.

## Best Practices

1. **Always run health checks** after starting servers
2. **Set `USE_SSE_MCP=false`** for offline development
3. **Monitor server logs** for errors
4. **Use startup script** to manage all servers
5. **Configure firewall** if accessing servers remotely

## Advanced Usage

### Custom Server URLs

```bash
# Use remote server
MCP_TRAFILATURA_URL=https://trafilatura.mycompany.com
```

### Load Balancing

Deploy multiple instances and use a load balancer:
```
nginx → {trafilatura-1:8001, trafilatura-2:8001}
```

### Docker Deployment

Each server can be containerized independently:
```dockerfile
FROM python:3.11
COPY mcp_servers/ /app/mcp_servers/
CMD ["python", "-m", "mcp_servers.trafilatura_sse"]
```

## Summary

The SSE architecture provides:
- ✅ Independent, scalable services
- ✅ HTTP/REST protocol (universally supported)
- ✅ Automatic fallback to direct calls
- ✅ Easy monitoring and debugging
- ✅ Remote server support
- ✅ Zero downtime deployments

This makes the system more robust, scalable, and production-ready compared to stdio-based servers.

