from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
client = os.environ["GOOGLE_CLIENT_SECRET_PATH"]
token = os.environ["GOOGLE_DRIVE_TOKEN_PATH"]

creds = None
if os.path.exists(token):
    creds = Credentials.from_authorized_user_file(token, SCOPES)
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(client, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(token, "w") as f: f.write(creds.to_json())

drive = build("drive", "v3", credentials=creds)
file_id = "<PASTE_SPREADSHEET_ID>"  # Sheets file is also a Drive file
perm = {"type":"anyone","role":"reader"}
resp = drive.permissions().create(fileId=file_id, body=perm).execute()
print("Drive sharing OK")

import certifi, os
ca = certifi.where()
print("Using CA bundle:", ca)
os.environ["SSL_CERT_FILE"] = ca
os.environ["REQUESTS_CA_BUNDLE"] = ca
print("Export these in your shell or .env:")
print("SSL_CERT_FILE=", ca)
print("REQUESTS_CA_BUNDLE=", ca)