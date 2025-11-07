"""
MCP SSE server for MuPDF4LLM (PDF to Markdown conversion).
"""

import os
import sys
from typing import Any, Dict
import pymupdf4llm

# Support both direct execution and module import
try:
    from .sse_base import SSEMCPServer, run_server
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_servers.sse_base import SSEMCPServer, run_server


class MuPDF4LLMSSEServer(SSEMCPServer):
    """SSE MCP server for PDF to Markdown conversion."""
    
    def __init__(self):
        super().__init__(name="mupdf4llm-sse", version="0.1.0")
        self.tools = {
            "convert": self.convert
        }
    
    async def convert(self, path: str) -> Dict[str, Any]:
        """
        Convert PDF to Markdown with images.
        
        Args:
            path: Path to PDF file
            
        Returns:
            Dict with markdown content and metadata
        """
        try:
            markdown = pymupdf4llm.to_markdown(path)
            
            # Extract image references (if any)
            import re
            images = re.findall(r'!\[.*?\]\((.*?)\)', markdown)
            
            return {
                "markdown": markdown,
                "images": images,
                "path": path
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_tools_list(self) -> list:
        return [
            {
                "name": "convert",
                "description": "Convert PDF to Markdown with images",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to PDF file"}
                    },
                    "required": ["path"]
                }
            }
        ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MuPDF4LLM SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8002, help="Server port")
    args = parser.parse_args()
    
    server = MuPDF4LLMSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

