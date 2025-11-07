"""
MCP SSE server for Gmail operations.
"""

import os
import sys
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re
from typing import Any, Dict, List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Support both direct execution and module import
try:
    from .sse_base import SSEMCPServer, run_server
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_servers.sse_base import SSEMCPServer, run_server

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailSSEServer(SSEMCPServer):
    """SSE MCP server for Gmail operations."""
    
    def __init__(self):
        super().__init__(name="gmail-sse", version="0.1.0")
        self.tools = {
            "send": self.send
        }
        self.creds = None
    
    def _get_credentials(self):
        """Get or refresh Google credentials."""
        if self.creds and self.creds.valid:
            return self.creds
        
        token_path = os.environ.get('GOOGLE_GMAIL_TOKEN_PATH', 'gmail_token.json')
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
    
    async def send(
        self,
        to: str,
        subject: str,
        html: str = "",
        attachments: List[str] = None
    ) -> Dict[str, Any]:
        """Send email via Gmail."""
        try:
            creds = self._get_credentials()
            service = build('gmail', 'v1', credentials=creds)
            
            message = MIMEMultipart()
            
            # Parse recipients
            recipients: List[str] = []
            if isinstance(to, str):
                parts = [p.strip() for p in re.split(r"[,;\s]+", to) if p and p.strip()]
                for p in parts:
                    m = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", p)
                    if m:
                        recipients.append(m.group(1))
            
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
                return {"error": "Invalid To header: no valid recipient email found"}
            
            message['To'] = ", ".join(recipients)
            message['Subject'] = subject.strip() if subject else ""
            
            if html:
                message.attach(MIMEText(html, 'html', _charset='utf-8'))
            
            if attachments:
                for file_path in attachments:
                    if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            message.attach(part)
            
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
    
    def get_tools_list(self) -> list:
        return [
            {
                "name": "send",
                "description": "Send email via Gmail",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "html": {"type": "string"},
                        "attachments": {"type": "array"}
                    },
                    "required": ["to", "subject"]
                }
            }
        ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gmail SSE MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8006, help="Server port")
    args = parser.parse_args()
    
    server = GmailSSEServer()
    run_server(server, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

