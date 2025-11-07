"""
Base class for SSE-based MCP servers.

Provides HTTP server with SSE endpoints for MCP protocol.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from aiohttp import web
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSEMCPServer:
    """Base class for SSE-based MCP servers."""
    
    def __init__(self, name: str, version: str = "0.1.0"):
        """
        Initialize SSE MCP server.
        
        Args:
            name: Server name
            version: Server version
        """
        self.name = name
        self.version = version
        self.tools = {}
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Set up HTTP routes for MCP protocol."""
        self.app.router.add_post('/mcp/initialize', self.handle_initialize)
        self.app.router.add_get('/mcp/tools/list', self.handle_tools_list)
        self.app.router.add_post('/mcp/tools/call', self.handle_tools_call)
        self.app.router.add_get('/mcp/sse', self.handle_sse)
        self.app.router.add_get('/health', self.handle_health)
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "ok", "server": self.name})
    
    async def handle_initialize(self, request: web.Request) -> web.Response:
        """Handle MCP initialize request."""
        try:
            data = await request.json()
            response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
            return web.json_response(response)
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_tools_list(self, request: web.Request) -> web.Response:
        """Handle tools/list request."""
        try:
            tools_list = self.get_tools_list()
            return web.json_response({"tools": tools_list})
        except Exception as e:
            logger.error(f"Error in tools/list: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_tools_call(self, request: web.Request) -> web.Response:
        """Handle tools/call request."""
        try:
            data = await request.json()
            tool_name = data.get("name")
            args = data.get("arguments", {})
            
            if tool_name not in self.tools:
                return web.json_response(
                    {"error": f"Unknown tool: {tool_name}"},
                    status=404
                )
            
            # Call the tool
            result = await self.tools[tool_name](**args)
            
            response = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result)
                    }
                ]
            }
            return web.json_response(response)
        except Exception as e:
            logger.error(f"Error in tools/call: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_sse(self, request: web.Request) -> web.StreamResponse:
        """Handle SSE connection for real-time updates."""
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        
        await response.prepare(request)
        
        try:
            # Send initial connection message
            await response.write(
                f"data: {json.dumps({'type': 'connected', 'server': self.name})}\n\n".encode()
            )
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                # Send heartbeat
                await response.write(b"data: {\"type\": \"heartbeat\"}\n\n")
                
        except asyncio.CancelledError:
            logger.info("SSE connection closed")
        finally:
            await response.write_eof()
        
        return response
    
    def get_tools_list(self) -> list:
        """
        Get list of available tools.
        
        Subclasses should override this method to provide tool schemas.
        
        Returns:
            List of tool definitions
        """
        return []
    
    async def run(self, host: str = '127.0.0.1', port: int = 8000):
        """
        Run the SSE MCP server.
        
        Args:
            host: Server host
            port: Server port
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"🚀 {self.name} SSE MCP Server running on http://{host}:{port}")
        logger.info(f"   Health: http://{host}:{port}/health")
        logger.info(f"   Tools: http://{host}:{port}/mcp/tools/list")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info(f"Shutting down {self.name}")
        finally:
            await runner.cleanup()


def run_server(server_instance: SSEMCPServer, host: str = '127.0.0.1', port: int = 8000):
    """
    Helper function to run an SSE MCP server.
    
    Args:
        server_instance: Instance of SSEMCPServer
        host: Server host
        port: Server port
    """
    import sys
    import platform
    
    # Fix for Windows - use proper event loop policy
    if sys.platform == 'win32' or platform.system() == 'Windows':
        # Set the event loop policy for Windows
        if sys.version_info >= (3, 8):
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except AttributeError:
                pass
    
    asyncio.run(server_instance.run(host, port))

