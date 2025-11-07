# Google Cloud Credentials Setup Guide

## ❌ Current Error
```
Credentials file not found: credentials.json
```

## ✅ Solution: Create Google Cloud Service Account

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account

### Step 2: Create or Select a Project
1. Click on the project dropdown at the top
2. Click "NEW PROJECT" or select an existing project
3. Give it a name like "F1-Standings-Bot"

### Step 3: Enable Required APIs
Enable these 3 APIs for your project:

1. **Google Sheets API**
   - Go to: https://console.cloud.google.com/apis/library/sheets.googleapis.com
   - Click "ENABLE"

2. **Google Drive API**
   - Go to: https://console.cloud.google.com/apis/library/drive.googleapis.com
   - Click "ENABLE"

3. **Gmail API**
   - Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com
   - Click "ENABLE"

### Step 4: Create Service Account
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "CREATE SERVICE ACCOUNT"
3. Enter details:
   - **Name**: `f1-bot-service-account`
   - **Description**: `Service account for F1 standings bot`
4. Click "CREATE AND CONTINUE"
5. Skip "Grant this service account access to project" (optional)
6. Click "DONE"

### Step 5: Create and Download Key
1. Click on the service account you just created
2. Go to the "KEYS" tab
3. Click "ADD KEY" → "Create new key"
4. Select **JSON** format
5. Click "CREATE"
6. A file will download automatically (named something like `project-name-123abc.json`)

### Step 6: Rename and Move the File
1. Rename the downloaded file to: `credentials.json`
2. Move it to your project directory:
   ```
   C:\Users\slalwani\OneDrive - QuidelOrtho\SUNIL\EAG\Session 8\code1\credentials.json
   ```

### Step 7: Update .env File
Make sure your `.env` file has the correct email:
```env
SELF_EMAIL=your_email@example.com
```

### Step 8: Restart the System
After placing the credentials file:
```powershell
# Stop all processes
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# Restart SSE servers
python start_sse_servers.py
```

Then restart the Telegram bot in another terminal:
```powershell
python .cursor\telegram_poller.py
```

## 📝 Important Notes

1. **Keep credentials.json SECURE** - Don't share it or commit it to git
2. The `.gitignore` file should already exclude `credentials.json`
3. Make sure the service account email has access to create sheets
4. For sending Gmail, you may need to set up additional OAuth consent

## 🔍 Verify Setup
After placing the file, run:
```powershell
python -c "import json; print('✅ Valid JSON' if json.load(open('credentials.json')) else '❌ Invalid')"
```

## ❓ Still Having Issues?

Check if the file is in the right location:
```powershell
Test-Path ".\credentials.json"
```

Should return `True`.

