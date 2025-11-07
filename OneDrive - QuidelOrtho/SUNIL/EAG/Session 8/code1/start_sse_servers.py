#!/usr/bin/env python3
"""
Startup script to run all SSE MCP servers.

Starts all 7 MCP servers on different ports and manages their lifecycle.
"""

import asyncio
import subprocess
import sys
import time
import requests
from pathlib import Path

# Server configurations
SERVERS = [
    {"name": "Trafilatura", "module": "mcp_servers.trafilatura_sse", "port": 8001},
    {"name": "MuPDF4LLM", "module": "mcp_servers.mupdf4llm_sse", "port": 8002},
    {"name": "Gemma Caption", "module": "mcp_servers.gemma_caption_sse", "port": 8003},
    {"name": "Google Sheets", "module": "mcp_servers.google_sheets_sse", "port": 8004},
    {"name": "Google Drive", "module": "mcp_servers.google_drive_sse", "port": 8005},
    {"name": "Gmail", "module": "mcp_servers.gmail_sse", "port": 8006},
    {"name": "Telegram", "module": "mcp_servers.telegram_sse", "port": 8007},
]


class SSEServerManager:
    """Manages multiple SSE MCP servers."""
    
    def __init__(self):
        self.processes = []
    
    async def start_all(self):
        """Start all SSE MCP servers."""
        print("=" * 60)
        print("🚀 Starting SSE MCP Servers")
        print("=" * 60)
        
        for server in SERVERS:
            try:
                print(f"\n[{server['name']}] Starting on port {server['port']}...")
                
                # On Windows, use CREATE_NEW_PROCESS_GROUP to properly manage subprocesses
                creation_flags = 0
                if sys.platform == 'win32':
                    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
                
                process = subprocess.Popen(
                    [sys.executable, "-m", server["module"], "--port", str(server["port"])],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Capture stderr to stdout
                    text=True,
                    bufsize=1,  # Line buffered
                    creationflags=creation_flags
                )
                
                self.processes.append({
                    "name": server["name"],
                    "port": server["port"],
                    "process": process
                })
                
                # Wait a bit for server to start
                await asyncio.sleep(2)
                
                # Check if process is still running
                if process.poll() is not None:
                    # Process died, capture output
                    stdout, _ = process.communicate(timeout=1)
                    print(f"[{server['name']}] ❌ Process died immediately!")
                    print(f"   Output: {stdout[:200] if stdout else 'No output'}")
                    continue
                
                # Check if server is healthy
                if await self.check_health(server["port"]):
                    print(f"[{server['name']}] ✅ Running on http://localhost:{server['port']}")
                else:
                    print(f"[{server['name']}] ⚠️  Started but health check failed")
                    # Try to get some output
                    try:
                        stdout, _ = process.communicate(timeout=0.1)
                        if stdout:
                            print(f"   Output: {stdout[:200]}")
                    except:
                        pass
                
            except Exception as e:
                print(f"[{server['name']}] ❌ Failed to start: {e}")
        
        print("\n" + "=" * 60)
        print("✅ All servers started")
        print("=" * 60)
        print("\nServer Status:")
        for server in SERVERS:
            print(f"  • {server['name']:<20} http://localhost:{server['port']}")
        print("\nPress Ctrl+C to stop all servers")
        print("=" * 60)
    
    async def check_health(self, port: int, max_retries: int = 5) -> bool:
        """Check if a server is healthy."""
        url = f"http://localhost:{port}/health"
        
        for i in range(max_retries):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                await asyncio.sleep(0.5)
        
        return False
    
    def stop_all(self):
        """Stop all running servers."""
        print("\n\n" + "=" * 60)
        print("🛑 Stopping SSE MCP Servers")
        print("=" * 60)
        
        for server_info in self.processes:
            try:
                print(f"[{server_info['name']}] Stopping...")
                
                # On Windows, send CTRL_BREAK_EVENT instead of terminate
                if sys.platform == 'win32':
                    try:
                        import signal
                        server_info["process"].send_signal(signal.CTRL_BREAK_EVENT)
                    except:
                        server_info["process"].terminate()
                else:
                    server_info["process"].terminate()
                
                server_info["process"].wait(timeout=5)
                print(f"[{server_info['name']}] ✅ Stopped")
            except subprocess.TimeoutExpired:
                print(f"[{server_info['name']}] ⚠️  Forcefully killing...")
                server_info["process"].kill()
                try:
                    server_info["process"].wait(timeout=2)
                except:
                    pass
            except Exception as e:
                print(f"[{server_info['name']}] ❌ Error stopping: {e}")
        
        print("=" * 60)
        print("✅ All servers stopped")
        print("=" * 60)
    
    async def monitor(self):
        """Monitor servers and keep them running."""
        try:
            while True:
                await asyncio.sleep(10)
                
                # Check if any process has died
                for server_info in self.processes:
                    if server_info["process"].poll() is not None:
                        print(f"\n⚠️  [{server_info['name']}] Process died! Exit code: {server_info['process'].returncode}")
        
        except KeyboardInterrupt:
            pass


async def main():
    """Main entry point."""
    manager = SSEServerManager()
    
    try:
        # Start all servers
        await manager.start_all()
        
        # Monitor servers
        await manager.monitor()
    
    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal...")
    
    finally:
        manager.stop_all()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the manager
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")

