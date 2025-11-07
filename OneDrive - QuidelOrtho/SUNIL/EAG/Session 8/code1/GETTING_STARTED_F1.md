# 🏎️ Getting Started: F1 Web Scraping to Google Sheets

## Complete Step-by-Step Guide

Follow these steps to scrape F1 2025 driver standings from Formula1.com and automatically create a Google Sheet.

---

## ✅ Step 1: Prerequisites Check

### 1.1 Verify Python Installation
```powershell
python --version
# Should show: Python 3.11 or higher
```

### 1.2 Check if Project Files Exist
```powershell
cd 'C:\Users\slalwani\OneDrive - QuidelOrtho\SUNIL\EAG\Session 8\code1'
ls
# You should see: agent/, mcp_servers/, start_sse_servers.py, etc.
```

### 1.3 Install Dependencies (if not already done)
```powershell
pip install -r requirements.txt
# OR if using uv:
uv sync
```

---

## 🔧 Step 2: Configure Environment Variables

### 2.1 Copy Environment Template
```powershell
Copy-Item env.example .env
```

### 2.2 Edit `.env` File

Open `.env` in a text editor and update these values:

```env
# ===== REQUIRED: Your Email =====
SELF_EMAIL=your_actual_email@example.com

# ===== REQUIRED: Telegram Bot =====
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# ===== F1 Configuration (already correct) =====
F1_STANDINGS_URL=https://www.formula1.com/en/results/2025/drivers

# ===== SSE Mode (already correct) =====
USE_SSE_MCP=true
MCP_TRAFILATURA_URL=http://localhost:8001
MCP_SHEETS_URL=http://localhost:8004
MCP_DRIVE_URL=http://localhost:8005
MCP_GMAIL_URL=http://localhost:8006
MCP_TELEGRAM_URL=http://localhost:8007
```

**Important**: Replace:
- `your_actual_email@example.com` with YOUR email
- `your_telegram_bot_token_here` with your bot token
- `your_chat_id_here` with your Telegram chat ID

### 2.3 Get Telegram Bot Token (if you don't have one)

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the token (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
5. Paste it in `.env` as `TELEGRAM_BOT_TOKEN`

### 2.4 Get Your Telegram Chat ID

**Method 1**: Simple way
1. Start a chat with your bot
2. Send any message (like "hello")
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}`
5. Copy that number and put it in `.env` as `TELEGRAM_CHAT_ID`

**Method 2**: Use @userinfobot
1. Search for `@userinfobot` in Telegram
2. Start the bot
3. It will show your ID
4. Copy and paste into `.env`

---

## 🔐 Step 3: Setup Google Cloud Credentials

### 3.1 Check if credentials.json Exists
```powershell
Test-Path .\credentials.json
# Should return: True
```

If it returns `False`, you need to set up Google Cloud credentials.

### 3.2 Enable Google APIs (CRITICAL!)

You **MUST** enable these 3 APIs:

**Option A: Use the Script I Created**
```powershell
# This will open browser tabs for each API
# Just click "ENABLE" on each one
.\enable_apis_interactive.ps1
```

**Option B: Manual Setup**

Open these 3 links and click "ENABLE" on each:

1. **Google Sheets API**: 
   https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=803760333185

2. **Google Drive API**:
   https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=803760333185

3. **Gmail API**:
   https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=803760333185

⏱️ **Wait 2-3 minutes** after enabling for APIs to activate.

---

## 🚀 Step 4: Start the Services

### 4.1 Open PowerShell Terminal #1 (for SSE Servers)

```powershell
cd 'C:\Users\slalwani\OneDrive - QuidelOrtho\SUNIL\EAG\Session 8\code1'
python start_sse_servers.py
```

**Expected output**:
```
🚀 Starting SSE MCP Servers
============================================================

[Trafilatura] Starting on port 8001...
[Trafilatura] ✅ Running on http://localhost:8001

[MuPDF4LLM] Starting on port 8002...
[MuPDF4LLM] ✅ Running on http://localhost:8002

... (continues for all 7 servers)

============================================================
✅ All servers started
============================================================

Press Ctrl+C to stop all servers
```

✅ **Leave this terminal running!**

### 4.2 Open PowerShell Terminal #2 (for Telegram Bot)

```powershell
cd 'C:\Users\slalwani\OneDrive - QuidelOrtho\SUNIL\EAG\Session 8\code1'
python .cursor\telegram_poller.py
```

**Expected output**:
```
============================================================
🤖 Telegram Bot Starting
============================================================

✅ Telegram API connection successful
✅ Bot user: @YourBotName
✅ SELF_EMAIL configured: your_email@example.com

🌐 MCP Mode: SSE (Server-Sent Events)
   Using SSE servers on localhost:8001-8007

============================================================
🚀 Bot is running! Send 'f1' to trigger workflow
============================================================

[INFO] Polling for updates...
```

✅ **Leave this terminal running too!**

---

## 📱 Step 5: Test the F1 Workflow

### 5.1 Send Message to Your Bot

1. Open Telegram on your phone or desktop
2. Find your bot (the one you created with BotFather)
3. Send this message:
   ```
   f1
   ```

### 5.2 Watch the Progress

In **Terminal #2** (telegram_poller.py), you'll see:

```
[DEBUG] Received message from chat 123456789: f1
[DEBUG] Detected F1 workflow trigger!
[DEBUG] Starting workflow execution...
[DEBUG] Workflow goal: Extract the 2025 F1 Driver Standings table from...

[INFO] Step 1: Extract 2025 F1 driver standings from web using Trafilatura
[INFO] ✅ Step completed

[INFO] Step 2: Create/update Google Sheet with 2025 F1 driver standings data
[INFO] ✅ Step completed

[INFO] Step 3: Create shareable link for the spreadsheet
[INFO] ✅ Step completed

[INFO] Step 4: Email sheet link
[INFO] ✅ Step completed

[DEBUG] Workflow result: success=True
```

### 5.3 Get Your Result

You'll receive **3 notifications**:

1. **Telegram Bot Reply**:
   ```
   ✅ Done. Sheet: https://docs.google.com/spreadsheets/d/[YOUR-ID]/edit
   ```

2. **Email** (to your SELF_EMAIL):
   - Subject: "F1 Standings Sheet"
   - Body: Link to your Google Sheet

3. **Google Sheets** (in your Google Drive):
   - Title: "F1_2025_Driver_Standings"
   - Sheet: "Drivers_2025"
   - Data: All 21 F1 drivers with current points

---

## 📊 Step 6: Verify Your Google Sheet

### 6.1 Open the Sheet

Click the link from Telegram or your email.

### 6.2 Expected Data Format

| Position | Driver | Nationality | Team | Points |
|----------|--------|-------------|------|--------|
| 1 | Lando Norris NOR | GBR | McLaren | 357 |
| 2 | Oscar Piastri PIA | AUS | McLaren | 356 |
| 3 | Max Verstappen VER | NED | Red Bull Racing | 321 |
| 4 | George Russell RUS | GBR | Mercedes | 258 |
| 5 | Charles Leclerc LEC | MON | Ferrari | 210 |
| ... | ... | ... | ... | ... |

**Total**: 21 rows (all F1 drivers for 2025 season)

---

## 🔍 Troubleshooting

### Problem 1: SSE Servers Won't Start

**Symptoms**:
```
❌ Port 8001 already in use
```

**Solution**:
```powershell
# Kill all Python processes
Stop-Process -Name python -Force

# Wait 5 seconds
Start-Sleep -Seconds 5

# Try again
python start_sse_servers.py
```

---

### Problem 2: "Google Sheets API not enabled"

**Error in Terminal**:
```
❌ Failed at: Create/update Google Sheet
Error: Google Sheets API has not been used in project 803760333185
```

**Solution**:
1. Click this link: https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=803760333185
2. Click the blue "ENABLE" button
3. Wait 2-3 minutes
4. Restart both terminals (Ctrl+C, then run again)
5. Try sending "f1" again

---

### Problem 3: "SELF_EMAIL not configured"

**Error**:
```
❌ Cannot run F1 workflow: SELF_EMAIL is not configured!
```

**Solution**:
```powershell
# Edit .env file
notepad .env

# Add this line (with YOUR email):
SELF_EMAIL=your_email@example.com

# Save and close

# Restart Terminal #2 (Telegram bot)
# Ctrl+C to stop, then:
python .cursor\telegram_poller.py
```

---

### Problem 4: Bot Doesn't Respond

**Symptoms**: You send "f1" but nothing happens

**Solution A**: Check Terminal #2 for errors

**Solution B**: Verify Telegram configuration
```powershell
# Check if bot token works
$token = "YOUR_BOT_TOKEN_HERE"
Invoke-WebRequest -Uri "https://api.telegram.org/bot$token/getMe"

# Should return bot info like:
# {"ok":true,"result":{"id":123456,"is_bot":true,"first_name":"YourBot"}}
```

**Solution C**: Check chat ID
```powershell
# Send a message to your bot first, then:
$token = "YOUR_BOT_TOKEN_HERE"
Invoke-WebRequest -Uri "https://api.telegram.org/bot$token/getUpdates"

# Look for your message and find "chat":{"id":XXXXXX}
# Make sure that ID matches TELEGRAM_CHAT_ID in .env
```

---

### Problem 5: Web Scraping Fails

**Error**:
```
❌ Failed at: Extract 2025 F1 driver standings
Error: HTTP 403 or timeout
```

**Solution**:
```powershell
# Test if URL is accessible
Invoke-WebRequest -Uri "https://www.formula1.com/en/results/2025/drivers"

# If that works, check if Trafilatura server is running
Invoke-WebRequest -Uri "http://localhost:8001/health"

# Should return: {"status": "ok"}
```

---

### Problem 6: No Email Received

**Symptoms**: Workflow completes but no email arrives

**Solutions**:

1. **Check spam folder** in your email

2. **Verify Gmail API is enabled**:
   https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=803760333185

3. **Check SELF_EMAIL in .env**:
   ```powershell
   notepad .env
   # Make sure SELF_EMAIL=your_actual_email@example.com
   ```

4. **Check Gmail server status**:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8006/health"
   ```

---

## 🎯 Quick Reference Commands

### Start Everything
```powershell
# Terminal 1
python start_sse_servers.py

# Terminal 2 (new window)
python .cursor\telegram_poller.py
```

### Stop Everything
```powershell
# In both terminals, press: Ctrl+C

# Or kill all:
Stop-Process -Name python -Force
```

### Restart After Configuration Changes
```powershell
# Terminal 1: Ctrl+C, then
python start_sse_servers.py

# Terminal 2: Ctrl+C, then
python .cursor\telegram_poller.py
```

### Check Server Health
```powershell
$ports = 8001,8004,8005,8006,8007
foreach ($port in $ports) {
    try {
        Invoke-WebRequest -Uri "http://localhost:$port/health" -TimeoutSec 2 | Out-Null
        Write-Host "✅ Port $port OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ Port $port FAILED" -ForegroundColor Red
    }
}
```

### View Logs (if issues occur)
```powershell
# Check what's in Terminal 1 and Terminal 2
# All output is printed to console
```

---

## 📋 Configuration Checklist

Before running, make sure:

- [ ] `.env` file exists and has your values
- [ ] `SELF_EMAIL` is set to your real email
- [ ] `TELEGRAM_BOT_TOKEN` is set
- [ ] `TELEGRAM_CHAT_ID` is set
- [ ] `credentials.json` exists in project root
- [ ] Google Sheets API is enabled
- [ ] Google Drive API is enabled
- [ ] Gmail API is enabled
- [ ] Both terminals are running (SSE servers + Bot)

---

## 🎉 Success Indicators

You know it's working when:

1. ✅ Both terminals show no errors
2. ✅ You can send messages to your Telegram bot
3. ✅ Bot responds with "✅ Done. Sheet: [URL]"
4. ✅ You receive an email with the Google Sheets link
5. ✅ Google Sheet contains 21 F1 drivers with current points
6. ✅ Sheet is titled "F1_2025_Driver_Standings"

---

## 📞 Need More Help?

### Check Documentation
- `README.md` - Project overview
- `docs/F1_2025_WORKFLOW.md` - Detailed workflow explanation
- `docs/SETUP_GUIDE.md` - Complete setup guide
- `ENABLE_GOOGLE_APIS.md` - API setup help

### Common Issues Guide
- `FIX_APIS_GUIDE.md` - API troubleshooting
- `OAUTH_SETUP.md` - OAuth configuration

---

## 🔄 Next Steps

Once the basic workflow is running, you can:

1. **Customize the workflow**: Edit `.cursor/telegram_poller.py`
2. **Change the sheet format**: Modify `agent/decision/planner.py`
3. **Add more data sources**: Create new MCP servers
4. **Schedule automatic updates**: Add cron jobs or Windows Task Scheduler

---

**🏁 You're all set! Send "f1" to your Telegram bot and watch the magic happen!** 🏎️

