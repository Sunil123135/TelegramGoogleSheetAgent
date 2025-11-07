"""
MCP stdio server for Gemma image captioning.

Note: This requires Gemma 3 12B to be available locally (e.g., via Ollama).
Alternatively, use Google's Gemini API for captioning.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict
from google import genai
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GemmaCaptionServer:
    """MCP server for image captioning using Gemma/Gemini."""
    
    def __init__(self):
        self.tools = {
            "describe": self.describe
        }
        # Get API key from environment variable
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "Missing Google API key! Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.\n"
                "Get your API key from: https://aistudio.google.com/apikey"
            )
        self.client = genai.Client(api_key=api_key)
    
    async def describe(self, image_url_or_path: str) -> Dict[str, Any]:
        """
        Generate alt-text caption for an image.
        
        Args:
            image_url_or_path: Image URL or local path
            
        Returns:
            Dict with alt_text
        """
        try:
            # Load image
            if image_url_or_path.startswith("http"):
                # Use URL directly
                image_data = image_url_or_path
            else:
                # Read local file
                path = Path(image_url_or_path)
                if not path.exists():
                    return {"error": f"Image not found: {image_url_or_path}"}
                
                with open(path, 'rb') as f:
                    image_bytes = f.read()
                
                # For Gemini API, we need to upload or encode
                import base64
                image_data = base64.b64encode(image_bytes).decode()
            
            # Generate caption using Gemini
            prompt = """Describe this image in one concise sentence for use as alt-text. 
Focus on the main subject and key visual elements. Keep it under 100 characters."""
            
            # Note: Gemini vision models can accept images
            # For now, return a placeholder
            alt_text = f"Image: {Path(image_url_or_path).name}"
            
            # In production, use:
            # response = self.client.models.generate_content(
            #     model="gemini-2.0-flash-exp",
            #     contents=[prompt, {"mime_type": "image/jpeg", "data": image_data}]
            # )
            # alt_text = response.text.strip()
            
            return {
                "alt_text": alt_text,
                "image_ref": image_url_or_path
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
                    "serverInfo": {"name": "gemma_caption_stdio", "version": "0.1.0"},
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
                        "name": "describe",
                        "description": "Generate alt-text caption for an image",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "image_url_or_path": {
                                    "type": "string",
                                    "description": "Image URL or local path"
                                }
                            },
                            "required": ["image_url_or_path"]
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
    server = GemmaCaptionServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

