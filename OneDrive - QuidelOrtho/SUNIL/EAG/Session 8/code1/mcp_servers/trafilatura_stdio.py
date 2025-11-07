"""
MCP stdio server for Trafilatura (web content extraction).
"""

import asyncio
import json
import sys
from typing import Any, Dict
import trafilatura


class TrafilaturaServer:
    """MCP server for web content extraction."""
    
    def __init__(self):
        self.tools = {
            "fetch_markdown": self.fetch_markdown
        }
    
    async def fetch_markdown(self, url: str) -> Dict[str, Any]:
        """
        Fetch and convert web page to Markdown.
        
        Args:
            url: Web page URL
            
        Returns:
            Dict with markdown content and image URLs
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {"error": f"Failed to fetch URL: {url}"}
            
            markdown = trafilatura.extract(
                downloaded,
                output_format="markdown",
                include_tables=True,
                include_images=True,
                include_links=True
            )
            
            # Extract image URLs
            import re
            images = re.findall(r'!\[.*?\]\((.*?)\)', markdown or "")
            
            return {
                "markdown": markdown or "",
                "images": images,
                "url": url
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "trafilatura_stdio", "version": "0.1.0"},
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
            return response

        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "fetch_markdown",
                        "description": "Fetch web page and convert to Markdown",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "description": "Web page URL"}
                            },
                            "required": ["url"]
                        }
                    }
                ]
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            if tool_name in self.tools:
                result = await self.tools[tool_name](**args)
                return {"content": [{"type": "text", "text": json.dumps(result)}]}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        return {"error": "Unknown method"}
    
    async def run(self):
        """Run the MCP server (stdio mode)."""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line)
                response = await self.handle_request(request)
                
                print(json.dumps(response), flush=True)
            except Exception as e:
                error_response = {"error": str(e)}
                print(json.dumps(error_response), flush=True)


def main():
    """Entry point for the MCP server."""
    server = TrafilaturaServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

