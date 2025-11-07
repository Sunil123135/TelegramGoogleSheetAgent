"""
MCP stdio server for Gmail operations.
"""

import asyncio
import json
import sys
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
import re
from typing import Any, Dict, List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailServer:
    """MCP server for Gmail operations."""
    
    def __init__(self):
        self.tools = {
            "send": self.send
        }
        self.creds = None
    
    def _get_credentials(self):
        """Get or refresh Google credentials."""
        if self.creds and self.creds.valid:
            return self.creds
        
        # Get paths from environment with defaults
        token_path = os.environ.get('GOOGLE_GMAIL_TOKEN_PATH', 'gmail_token.json')
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
    
    async def send(
        self,
        to: str,
        subject: str,
        html: str = "",
        attachments: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML email body
            attachments: List of file paths to attach
            
        Returns:
            Dict with message_id
        """
        try:
            creds = self._get_credentials()
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message
            message = MIMEMultipart()

            # Sanitize and validate recipient(s)
            recipients: List[str] = []
            if isinstance(to, str):
                # Split by common separators and whitespace
                parts = [p.strip() for p in re.split(r"[,;\s]+", to) if p and p.strip()]
                for p in parts:
                    # Extract pure email if in Name <email> format
                    m = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", p)
                    if m:
                        recipients.append(m.group(1))
            elif isinstance(to, list):
                for p in to:
                    if isinstance(p, str):
                        m = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", p)
                        if m:
                            recipients.append(m.group(1))

            # Deduplicate and validate; if empty, fallback to sender profile address
            recipients = list(dict.fromkeys(recipients))
            if not recipients:
                try:
                    profile = service.users().getProfile(userId='me').execute()
                    sender_addr = profile.get('emailAddress')
                    if sender_addr:
                        recipients = [sender_addr]
                except Exception:
                    pass

            if not recipients:
                return {"error": "Invalid To header: no valid recipient email found and could not resolve sender address"}

            message['To'] = ", ".join(recipients)
            # Optional: set From explicitly to the authenticated user
            try:
                if 'sender_addr' in locals() and sender_addr:
                    message['From'] = sender_addr
            except Exception:
                pass
            message['Subject'] = subject.strip() if subject else ""
            
            # Add HTML body
            if html:
                message.attach(MIMEText(html, 'html', _charset='utf-8'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    # Skip None or empty paths
                    if not file_path or not isinstance(file_path, str):
                        continue
                    # Only attach if file exists
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            message.attach(part)
                    else:
                        # Log warning but don't fail the email
                        print(f"Warning: Attachment file not found: {file_path}")
            
            # Send message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "message_id": send_message['id'],
                "to": to,
                "subject": subject
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
                    "serverInfo": {"name": "gmail_stdio", "version": "0.1.0"},
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
                        "description": "Send email via Gmail",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "to": {"type": "string"},
                                "subject": {"type": "string"},
                                "html": {"type": "string"},
                                "attachments": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["to", "subject"]
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
    server = GmailServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

