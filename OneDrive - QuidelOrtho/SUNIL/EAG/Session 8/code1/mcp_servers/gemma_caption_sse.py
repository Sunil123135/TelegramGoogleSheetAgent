"""
MCP SSE server for image captioning using Gemma/Gemini.
"""

import os
import sys
from typing import Any, Dict

# Support both direct execution and module import
try:
    from .sse_base import SSEMCPServer, run_server
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_servers.sse_base import SSEMCPServer, run_server

try:
    from google import genai
except ImportError:
    genai = None


class GemmaCaptionSSEServer(SSEMCPServer):
    """SSE MCP server for image captioning."""
    
    def __init__(self):
        super().__init__(name="gemma-caption-sse", version="0.1.0")
        self.tools = {
            "caption": self.caption
        }
        self.client = None
        if genai is not None:
            try:
                self.client = genai.Client()
            except Exception:
                pass
    
    async def caption(self, image_url_or_path: str) -> Dict[str, Any]:
        """
        Generate caption for an image.
        
        Args:
            image_url_or_path: Image URL or local file path
            
        Returns:
            Dict with caption text
        """
        try:
            if self.client is None:
                # Fallback placeholder caption
                return {
                    "caption": f"Image: {image_url_or_path}",
                    "alt_text": f"Image from {image_url_or_path}"
                }
            
            # Use Gemini for actual captioning
            prompt = f"Generate a detailed alt-text caption for this image: {image_url_or_path}"
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            caption = response.text.strip()
            
            return {
                "caption": caption,
                "alt_text": caption,
                "image_ref": image_url_or_path
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_tools_list(self) -> list:
        return [
            {
                "name": "caption",
                "description": "Generate alt-text caption for an image",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_url_or_path": {"type": "string"}
                    },
                    "required": ["image_url_or_path"]
                }
            }
        ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gemma Caption SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8003, help="Server port")
    args = parser.parse_args()
    
    server = GemmaCaptionSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

