"""
MCP stdio server for MuPDF4LLM (PDF extraction).
"""

import asyncio
import json
import sys
from typing import Any, Dict
import pymupdf4llm


class MuPDF4LLMServer:
    """MCP server for PDF to Markdown conversion."""
    
    def __init__(self):
        self.tools = {
            "to_markdown": self.to_markdown
        }
    
    async def to_markdown(self, path: str) -> Dict[str, Any]:
        """
        Convert PDF to Markdown with image references.
        
        Args:
            path: PDF file path or URL
            
        Returns:
            Dict with markdown content and image paths
        """
        try:
            # Download if URL
            if path.startswith("http"):
                import requests
                import tempfile
                import os
                
                response = requests.get(path)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(response.content)
                    temp_path = tmp.name
                
                markdown = pymupdf4llm.to_markdown(temp_path)
                os.unlink(temp_path)
            else:
                markdown = pymupdf4llm.to_markdown(path)
            
            # Extract image references
            import re
            images = re.findall(r'!\[.*?\]\((.*?)\)', markdown)
            
            return {
                "markdown": markdown,
                "images": images,
                "path": path
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
                    "serverInfo": {"name": "mupdf4llm_stdio", "version": "0.1.0"},
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
                        "name": "to_markdown",
                        "description": "Convert PDF to Markdown with images",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "PDF file path or URL"}
                            },
                            "required": ["path"]
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
    server = MuPDF4LLMServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

