"""
MCP SSE server for Trafilatura (web content extraction).
"""

import os
import sys
import trafilatura
import re
from typing import Any, Dict

# Support both direct execution and module import
try:
    from .sse_base import SSEMCPServer, run_server
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_servers.sse_base import SSEMCPServer, run_server


class TrafilaturaSSEServer(SSEMCPServer):
    """SSE MCP server for web content extraction."""
    
    def __init__(self):
        super().__init__(name="trafilatura-sse", version="0.1.0")
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
            images = re.findall(r'!\[.*?\]\((.*?)\)', markdown or "")
            
            return {
                "markdown": markdown or "",
                "images": images,
                "url": url
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_tools_list(self) -> list:
        """Return list of available tools."""
        return [
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


def main():
    """Entry point for the SSE MCP server."""
    import argparse
    parser = argparse.ArgumentParser(description="Trafilatura SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8001, help="Server port")
    args = parser.parse_args()
    
    server = TrafilaturaSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

