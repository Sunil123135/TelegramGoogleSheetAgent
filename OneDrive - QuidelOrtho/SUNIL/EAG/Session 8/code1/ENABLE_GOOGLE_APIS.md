# Enable Google APIs - Quick Fix

## ❌ Current Error
```
Google Sheets API has not been used in project 803760333185 before or it is disabled.
```

## ✅ Solution: Enable Required APIs

### Your Project ID: `803760333185`

You need to enable 3 APIs for your Google Cloud project. Click each link below:

---

## 1. Enable Google Sheets API ⭐ REQUIRED
**Click this link and enable:**
👉 https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=803760333185

**Steps:**
1. Click the link above
2. Click the blue **"ENABLE"** button
3. Wait for confirmation (should take 5-10 seconds)

---

## 2. Enable Google Drive API ⭐ REQUIRED
**Click this link and enable:**
👉 https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=803760333185

**Steps:**
1. Click the link above
2. Click the blue **"ENABLE"** button
3. Wait for confirmation

---

## 3. Enable Gmail API ⭐ REQUIRED
**Click this link and enable:**
👉 https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=803760333185

**Steps:**
1. Click the link above
2. Click the blue **"ENABLE"** button
3. Wait for confirmation

---

## ⏱️ After Enabling All APIs

**Wait 2-3 minutes** for the changes to propagate across Google's systems.

Then restart your services:

```powershell
# Stop all Python processes
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# Wait a moment
Start-Sleep -Seconds 2

# Restart SSE servers
python start_sse_servers.py
```

In another terminal:
```powershell
# Restart Telegram bot
python .cursor\telegram_poller.py
```

---

## ✅ Verification

After enabling the APIs and restarting, send a test message to your Telegram bot:
```
Get F1 standings and create a sheet
```

The workflow should now complete successfully!

---

## 🔍 Check API Status

To verify which APIs are enabled, visit:
https://console.cloud.google.com/apis/dashboard?project=803760333185

You should see:
- ✅ Google Sheets API
- ✅ Google Drive API  
- ✅ Gmail API

All showing as "Enabled"

