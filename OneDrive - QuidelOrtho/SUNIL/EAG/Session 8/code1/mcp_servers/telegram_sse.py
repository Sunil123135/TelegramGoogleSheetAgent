"""
MCP SSE server for Telegram bot operations.
"""

import os
import sys
from typing import Any, Dict
from telegram import Bot

# Support both direct execution and module import
try:
    from .sse_base import SSEMCPServer, run_server
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_servers.sse_base import SSEMCPServer, run_server


class TelegramSSEServer(SSEMCPServer):
    """SSE MCP server for Telegram operations."""
    
    def __init__(self):
        super().__init__(name="telegram-sse", version="0.1.0")
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
        """Send a message to a Telegram chat."""
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
    
    def get_tools_list(self) -> list:
        return [
            {
                "name": "send",
                "description": "Send a message to a Telegram chat",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string"},
                        "text": {"type": "string"}
                    },
                    "required": ["chat_id", "text"]
                }
            }
        ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Telegram SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8007, help="Server port")
    args = parser.parse_args()
    
    server = TelegramSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

