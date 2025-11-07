"""
MCP stdio server for Google Drive sharing operations.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveServer:
    """MCP server for Google Drive operations."""
    
    def __init__(self):
        self.tools = {
            "share": self.share
        }
        self.creds = None
    
    def _get_credentials(self):
        """Get or refresh Google credentials."""
        if self.creds and self.creds.valid:
            return self.creds
        
        # Get paths from environment with defaults
        token_path = os.environ.get('GOOGLE_DRIVE_TOKEN_PATH', 'drive_token.json')
        creds_path = os.environ.get('GOOGLE_CLIENT_SECRET_PATH', 'credentials.json')
        
        # Expand user home directory (~) and make paths absolute
        token_path = os.path.expanduser(token_path)
        creds_path = os.path.expanduser(creds_path)
        
        # If relative paths, make them relative to current working directory
        if not os.path.isabs(token_path):
            token_path = os.path.abspath(token_path)
        if not os.path.isabs(creds_path):
            creds_path = os.path.abspath(creds_path)
        
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(f"Credentials file not found: {creds_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())
        
        return self.creds
    
    async def share(
        self,
        file_id: str,
        role: str = "reader",
        type: str = "anyone",
        email: str = None
    ) -> Dict[str, Any]:
        """
        Share a Google Drive file.
        
        Args:
            file_id: Google Drive file ID
            role: Permission role (reader, writer, commenter)
            type: Permission type (user, group, domain, anyone)
            email: Email address (required if type is user)
            
        Returns:
            Dict with share link and permission_id
        """
        try:
            creds = self._get_credentials()
            service = build('drive', 'v3', credentials=creds)
            
            # Create permission
            permission = {
                'type': type,
                'role': role
            }
            
            if email and type == 'user':
                permission['emailAddress'] = email
            
            result = service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()
            
            # Get shareable link
            file = service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return {
                "link": file.get('webViewLink'),
                "file_id": file_id,
                "permission_id": result.get('id')
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
                    "serverInfo": {"name": "google_drive_stdio", "version": "0.1.0"},
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
                        "name": "share",
                        "description": "Share a Google Drive file with permissions",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_id": {"type": "string"},
                                "role": {"type": "string", "enum": ["reader", "writer", "commenter"], "default": "reader"},
                                "type": {"type": "string", "enum": ["user", "group", "domain", "anyone"], "default": "anyone"},
                                "email": {"type": "string"}
                            },
                            "required": ["file_id"]
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
    server = GoogleDriveServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()


