"""
MCP stdio server for Telegram bot operations.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict
from telegram import Bot


class TelegramServer:
    """MCP server for Telegram operations."""
    
    def __init__(self):
        self.tools = {
            "send": self.send
        }
        self.bot = None
    
    def _get_bot(self):
        """Get Telegram bot instance."""
        if self.bot is None:
            token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if not token:
                raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            self.bot = Bot(token=token)
        return self.bot
    
    async def send(self, chat_id: str, text: str) -> Dict[str, Any]:
        """
        Send a message to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            
        Returns:
            Dict with send status
        """
        try:
            bot = self._get_bot()
            message = await bot.send_message(chat_id=chat_id, text=text)
            
            return {
                "ok": True,
                "chat_id": chat_id,
                "message_id": message.message_id
            }
        except Exception as e:
            return {"error": str(e), "ok": False}
    
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
                    "serverInfo": {"name": "telegram_stdio", "version": "0.1.0"},
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
                        "name": "send",
                        "description": "Send message to Telegram chat",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "chat_id": {"type": "string", "description": "Chat ID"},
                                "text": {"type": "string", "description": "Message text"}
                            },
                            "required": ["chat_id", "text"]
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
    server = TelegramServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

