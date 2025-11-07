from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
client = os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
token = os.environ.get("GOOGLE_SHEETS_TOKEN_PATH")

if not client:
    print("❌ GOOGLE_CLIENT_SECRET_PATH not set in .env")
    exit(1)
if not token:
    print("❌ GOOGLE_SHEETS_TOKEN_PATH not set in .env")
    exit(1)

# Expand paths
client = os.path.expanduser(client)
token = os.path.expanduser(token)

print(f"📁 Client secret path: {client}")
print(f"📁 Token path: {token}")

creds = None
if os.path.exists(token):
    print("✅ Found existing token, loading...")
    creds = Credentials.from_authorized_user_file(token, SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Refreshing expired token...")
        creds.refresh(Request())
    else:
        print("🌐 Starting OAuth flow in browser...")
        flow = InstalledAppFlow.from_client_secrets_file(client, SCOPES)
        creds = flow.run_local_server(port=0)
        print("✅ OAuth completed!")
    
    # Save token
    with open(token, "w") as f:
        f.write(creds.to_json())
    print(f"💾 Token saved to {token}")

# Test with the spreadsheet
service = build("sheets", "v4", credentials=creds)
spreadsheet_id = "1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY"

print(f"\n📊 Testing write to spreadsheet: {spreadsheet_id}")

body = {
    "values": [
        ["Position", "Driver", "Team", "Points"],
        ["1", "Max Verstappen", "Red Bull", "400"],
        ["2", "Sergio Perez", "Red Bull", "285"],
        ["3", "Lewis Hamilton", "Mercedes", "234"]
    ]
}

try:
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body=body
    ).execute()
    
    print(f"✅ Sheets OK - Updated {result.get('updatedCells')} cells!")
    print(f"🔗 View at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
except Exception as e:
    print(f"❌ Error writing to sheet: {e}")
    print("\nMake sure:")
    print("  1. The spreadsheet exists")
    print("  2. You have write access to it")
    print("  3. The sheet name is correct (try 'Sheet1' instead of 'Standings')")


