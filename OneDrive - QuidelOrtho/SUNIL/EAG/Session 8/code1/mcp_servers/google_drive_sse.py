"""
MCP SSE server for Google Drive sharing operations.
"""

import os
import sys
from typing import Any, Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Support both direct execution and module import
try:
    from .sse_base import SSEMCPServer, run_server
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_servers.sse_base import SSEMCPServer, run_server

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveSSEServer(SSEMCPServer):
    """SSE MCP server for Google Drive operations."""
    
    def __init__(self):
        super().__init__(name="google-drive-sse", version="0.1.0")
        self.tools = {
            "share": self.share
        }
        self.creds = None
    
    def _get_credentials(self):
        """Get or refresh Google credentials."""
        if self.creds and self.creds.valid:
            return self.creds
        
        token_path = os.environ.get('GOOGLE_DRIVE_TOKEN_PATH', 'drive_token.json')
        creds_path = os.environ.get('GOOGLE_CLIENT_SECRET_PATH', 'credentials.json')
        
        token_path = os.path.abspath(os.path.expanduser(token_path))
        creds_path = os.path.abspath(os.path.expanduser(creds_path))
        
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
        """Share a Google Drive file."""
        try:
            creds = self._get_credentials()
            service = build('drive', 'v3', credentials=creds)
            
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
    
    def get_tools_list(self) -> list:
        return [
            {
                "name": "share",
                "description": "Share a Google Drive file with permissions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"},
                        "role": {"type": "string", "enum": ["reader", "writer", "commenter"]},
                        "type": {"type": "string", "enum": ["user", "group", "domain", "anyone"]},
                        "email": {"type": "string"}
                    },
                    "required": ["file_id"]
                }
            }
        ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Google Drive SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8005, help="Server port")
    args = parser.parse_args()
    
    server = GoogleDriveSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

