"""
MCP stdio server for Google Sheets operations.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class GoogleSheetsServer:
    """MCP server for Google Sheets operations."""
    
    def __init__(self):
        self.tools = {
            "upsert_table": self.upsert_table
        }
        self.creds = None
    
    def _get_credentials(self):
        """Get or refresh Google credentials."""
        if self.creds and self.creds.valid:
            return self.creds
        
        # Get paths from environment with defaults
        token_path = os.environ.get('GOOGLE_SHEETS_TOKEN_PATH', 'token.json')
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
                    error_msg = (
                        f"Credentials file not found: {creds_path}\n"
                        f"Please ensure the file exists at this location, or set GOOGLE_CLIENT_SECRET_PATH "
                        f"environment variable to point to your credentials.json file.\n"
                        f"Current working directory: {os.getcwd()}"
                    )
                    raise FileNotFoundError(error_msg)
                
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
        """
        Create or update a Google Sheet with data.
        
        Args:
            spreadsheet_title: Title of the spreadsheet
            sheet_name: Name of the sheet within the spreadsheet
            rows: 2D array of cell values
            
        Returns:
            Dict with spreadsheet_id and sheet_url
        """
        try:
            creds = self._get_credentials()
            service = build('sheets', 'v4', credentials=creds)
            
            # Create new spreadsheet
            spreadsheet = {
                'properties': {'title': spreadsheet_title},
                'sheets': [{'properties': {'title': sheet_name}}]
            }
            
            spreadsheet = service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            
            # Write data
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
                    "serverInfo": {"name": "google_sheets_stdio", "version": "0.1.0"},
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
                        "name": "upsert_table",
                        "description": "Create or update Google Sheet with data",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "spreadsheet_title": {"type": "string"},
                                "sheet_name": {"type": "string"},
                                "rows": {
                                    "type": "array",
                                    "items": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "required": ["spreadsheet_title", "sheet_name", "rows"]
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
    server = GoogleSheetsServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

