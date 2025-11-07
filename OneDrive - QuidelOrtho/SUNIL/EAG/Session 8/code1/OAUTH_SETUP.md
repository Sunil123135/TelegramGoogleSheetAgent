# Google Sheets OAuth Setup Guide

## Current Status
✅ Created `.env` file
✅ Created credentials directory at: `C:\Users\slalwani\.config\cursor-agent\google\`
⏳ Need to add Google OAuth credentials

## Steps to Complete

### Step 1: Get Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or Select Project**
   - Click the project dropdown at the top
   - Either create a new project or select an existing one

3. **Enable Google Sheets API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

4. **Create OAuth Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ CREATE CREDENTIALS" at the top
   - Select "OAuth client ID"
   
5. **Configure OAuth Consent Screen (if prompted)**
   - User Type: **External**
   - App name: "Cursor Agent"
   - User support email: your email
   - Developer contact: your email
   - Scopes: Add `https://www.googleapis.com/auth/spreadsheets`
   - Test users: Add your email
   - Click "Save and Continue"

6. **Create OAuth Client ID**
   - Application type: **Desktop app**
   - Name: "Cursor Agent Desktop"
   - Click "Create"

7. **Download Credentials**
   - Click the download icon (⬇️) next to your new credential
   - This downloads a JSON file (usually named `client_secret_xxxxx.json`)

### Step 2: Place Credentials File

Move the downloaded file to:
```
C:\Users\slalwani\.config\cursor-agent\google\client_secret.json
```

**PowerShell command:**
```powershell
# Replace xxxxx with your actual filename
Move-Item "$env:USERPROFILE\Downloads\client_secret_xxxxx.json" "$env:USERPROFILE\.config\cursor-agent\google\client_secret.json"
```

**Or manually:**
1. Open File Explorer
2. Navigate to your Downloads folder
3. Find the `client_secret_xxxxx.json` file
4. Copy it to `C:\Users\slalwani\.config\cursor-agent\google\`
5. Rename it to `client_secret.json`

### Step 3: Run OAuth Test Script

Once the credentials are in place:

```bash
python test_oauth.py
```

This will:
1. Open a browser for Google OAuth authorization
2. Ask you to select your Google account
3. Ask you to grant permissions to the app
4. Save the token to `C:\Users\slalwani\.config\cursor-agent\google\sheets_token.json`
5. Test writing data to your spreadsheet: https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY

### Step 4: Verify

If everything works, you should see:
```
✅ Sheets OK - Updated 12 cells!
🔗 View at: https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY
```

## Troubleshooting

### "Client secret not found"
- Make sure the file is named exactly `client_secret.json` (not `client_secret_xxxxx.json`)
- Check it's in the correct directory: `C:\Users\slalwani\.config\cursor-agent\google\`

### "Permission denied" when writing to sheet
- Make sure you have edit access to the spreadsheet
- If it's someone else's sheet, they need to share it with your Google account

### "Insufficient permissions"
- Go back to Google Cloud Console → OAuth consent screen
- Make sure the scope `https://www.googleapis.com/auth/spreadsheets` is added
- Add your email to "Test users"

### OAuth screen doesn't open
- Check if your firewall is blocking localhost connections
- Try manually visiting the URL that appears in the terminal

## What's Configured

Your `.env` file now has:
```bash
GOOGLE_CLIENT_SECRET_PATH=~/.config/cursor-agent/google/client_secret.json
GOOGLE_SHEETS_TOKEN_PATH=~/.config/cursor-agent/google/sheets_token.json
F1_OUTPUT_SHEET_URL=https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY/edit?usp=drive_link
F1_OUTPUT_SHEET_ID=1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY
```

## Next Steps After OAuth Works

Once OAuth is working, you can:

1. **Run the F1 workflow:**
   ```bash
   python main.py f1
   ```

2. **Run interactive mode:**
   ```bash
   python main.py interactive
   ```

3. **Use the agent in your own scripts:**
   ```python
   from agent.orchestrator import CursorAgent
   import asyncio
   
   async def main():
       agent = CursorAgent()
       result = await agent.execute_workflow("Your goal here")
   
   asyncio.run(main())
   ```

---

**Ready?** Place your `client_secret.json` file and run `python test_oauth.py`

