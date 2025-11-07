"""
SSE-based MCP client for agent communication.

Handles HTTP requests to SSE MCP servers.
"""

import aiohttp
import asyncio
import json
from typing import Any, Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSEMCPClient:
    """Client for communicating with SSE MCP servers."""
    
    def __init__(self, server_url: str, timeout: int = 30):
        """
        Initialize SSE MCP client.
        
        Args:
            server_url: Base URL of the MCP server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def health_check(self) -> bool:
        """
        Check if server is healthy.
        
        Returns:
            True if server is responding
        """
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "ok"
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection with MCP server.
        
        Returns:
            Server info and capabilities
        """
        try:
            await self._ensure_session()
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            }
            
            async with self.session.post(
                f"{self.server_url}/mcp/initialize",
                json=request_data
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Initialize failed: {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.server_url}/mcp/tools/list") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("tools", [])
        except Exception as e:
            logger.error(f"List tools failed: {e}")
            raise
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            await self._ensure_session()
            request_data = {
                "name": tool_name,
                "arguments": arguments
            }
            
            async with self.session.post(
                f"{self.server_url}/mcp/tools/call",
                json=request_data
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Extract result from MCP response format
                if "content" in data and len(data["content"]) > 0:
                    content_text = data["content"][0].get("text", "{}")
                    return json.loads(content_text)
                elif "error" in data:
                    raise RuntimeError(data["error"])
                else:
                    return data
        except Exception as e:
            logger.error(f"Tool call failed ({tool_name}): {e}")
            raise
    
    async def close(self):
        """Close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()


class SSEMCPClientPool:
    """Pool of SSE MCP clients for multiple servers."""
    
    def __init__(self, server_configs: Dict[str, str]):
        """
        Initialize client pool.
        
        Args:
            server_configs: Dict mapping server name to URL
                           e.g., {"trafilatura": "http://localhost:8001"}
        """
        self.server_configs = server_configs
        self.clients: Dict[str, SSEMCPClient] = {}
    
    async def get_client(self, server_name: str) -> SSEMCPClient:
        """
        Get or create client for a server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            SSE MCP client instance
        """
        if server_name not in self.clients:
            if server_name not in self.server_configs:
                raise ValueError(f"Unknown server: {server_name}")
            
            url = self.server_configs[server_name]
            self.clients[server_name] = SSEMCPClient(url)
        
        return self.clients[server_name]
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on a specific server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        client = await self.get_client(server_name)
        return await client.call_tool(tool_name, arguments)
    
    async def close_all(self):
        """Close all client connections."""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()


# Singleton instance
_client_pool: Optional[SSEMCPClientPool] = None


def get_client_pool() -> SSEMCPClientPool:
    """
    Get the global SSE MCP client pool.
    
    Returns:
        SSE MCP client pool instance
    """
    global _client_pool
    if _client_pool is None:
        # Default server configurations
        from os import environ
        
        server_configs = {
            "trafilatura": environ.get("MCP_TRAFILATURA_URL", "http://localhost:8001"),
            "mupdf4llm": environ.get("MCP_MUPDF4LLM_URL", "http://localhost:8002"),
            "gemma": environ.get("MCP_GEMMA_URL", "http://localhost:8003"),
            "google_sheets": environ.get("MCP_SHEETS_URL", "http://localhost:8004"),
            "google_drive": environ.get("MCP_DRIVE_URL", "http://localhost:8005"),
            "gmail": environ.get("MCP_GMAIL_URL", "http://localhost:8006"),
            "telegram": environ.get("MCP_TELEGRAM_URL", "http://localhost:8007"),
        }
        
        _client_pool = SSEMCPClientPool(server_configs)
    
    return _client_pool

