"""
MCP SSE server for Google Sheets operations.
"""

import os
import sys
from typing import Any, Dict, List
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

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class GoogleSheetsSSEServer(SSEMCPServer):
    """SSE MCP server for Google Sheets operations."""
    
    def __init__(self):
        super().__init__(name="google-sheets-sse", version="0.1.0")
        self.tools = {
            "upsert_table": self.upsert_table
        }
        self.creds = None
    
    def _get_credentials(self):
        """Get or refresh Google credentials."""
        if self.creds and self.creds.valid:
            return self.creds
        
        token_path = os.environ.get('GOOGLE_SHEETS_TOKEN_PATH', 'token.json')
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
    
    async def upsert_table(
        self,
        spreadsheet_title: str,
        sheet_name: str,
        rows: List[List[str]]
    ) -> Dict[str, Any]:
        """Create or update a Google Sheet with data."""
        try:
            creds = self._get_credentials()
            service = build('sheets', 'v4', credentials=creds)
            
            spreadsheet = {
                'properties': {'title': spreadsheet_title},
                'sheets': [{'properties': {'title': sheet_name}}]
            }
            
            spreadsheet = service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            range_name = f"{sheet_name}!A1"
            body = {'values': rows}
            
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
            return {
                "spreadsheet_id": spreadsheet_id,
                "sheet_url": sheet_url,
                "rows_inserted": len(rows)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_tools_list(self) -> list:
        return [
            {
                "name": "upsert_table",
                "description": "Create or update a Google Sheet with data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "spreadsheet_title": {"type": "string"},
                        "sheet_name": {"type": "string"},
                        "rows": {"type": "array"}
                    },
                    "required": ["spreadsheet_title", "sheet_name", "rows"]
                }
            }
        ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Google Sheets SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8004, help="Server port")
    args = parser.parse_args()
    
    server = GoogleSheetsSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

