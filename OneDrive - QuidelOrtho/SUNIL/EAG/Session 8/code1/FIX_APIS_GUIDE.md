# 🔧 Fix: Enable Google APIs

## Current Status
❌ **Error:** Google Sheets API not enabled  
✅ **Actions Taken:** Stopped services, opened browser tabs, created restart scripts

---

## 🎯 What You Need to Do (4 Steps)

### Step 1: Enable APIs in Browser ⏱️ 2 minutes

**3 browser tabs should be open now.** In each tab:

1. Look for the **blue "ENABLE" button**
2. Click it
3. Wait for "API enabled" confirmation (5-10 seconds)

**All 3 tabs:**
- ✅ Google Sheets API
- ✅ Google Drive API
- ✅ Gmail API

**Tabs didn't open?** Visit this link:
```
https://console.developers.google.com/apis/dashboard?project=803760333185
```
Then click on each API and enable it.

---

### Step 2: Wait ⏱️ 1-2 minutes

After enabling all 3 APIs, **wait 1-2 minutes** for the changes to propagate across Google's systems.

Get a coffee ☕

---

### Step 3: Restart Services ⏱️ 30 seconds

Run this command in PowerShell:

```powershell
.\quick_restart.ps1
```

This will:
- Stop all services
- Start 7 SSE servers
- Start Telegram bot
- Verify everything is healthy

---

### Step 4: Test! 🚀

Send this message to your Telegram bot:
```
Get F1 standings and create a sheet
```

**Expected result:**
1. ✅ Extracts F1 standings
2. ✅ Creates Google Sheet
3. ✅ Shares the sheet
4. ✅ Emails you the link

---

## 🆘 Troubleshooting

### "APIs still not working after restart"
- **Solution:** Wait another 2-3 minutes and run `.\quick_restart.ps1` again

### "Can't find the ENABLE button"
- **Solution:** You might already be signed in to Google
  - Look for "API enabled" status
  - If it says "DISABLE" button, the API is already enabled ✅

### "Browser tabs didn't open"
- **Solution:** Manually visit each URL:
  - Sheets: https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=803760333185
  - Drive: https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=803760333185
  - Gmail: https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=803760333185

---

## 📁 Files Created

- ✅ `quick_restart.ps1` - Simple restart script (recommended)
- ✅ `enable_apis_interactive.ps1` - Interactive restart with prompts
- ✅ `ENABLE_GOOGLE_APIS.md` - Detailed API setup guide
- ✅ `FIX_APIS_GUIDE.md` - This guide

---

## 📊 System Architecture

```
┌─────────────────┐
│ Telegram Bot    │ ← You send messages here
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Executor  │ ← Orchestrates workflow
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         7 SSE Servers                   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Trafilatura  │  │ Google       │   │
│  │ (Web Extract)│  │ Sheets       │   │ ← APIs needed here!
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ MuPDF4LLM    │  │ Google       │   │
│  │ (PDF Extract)│  │ Drive        │   │ ← APIs needed here!
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Gemma        │  │ Gmail        │   │ ← APIs needed here!
│  │ (Captions)   │  └──────────────┘   │
│  └──────────────┘  ┌──────────────┐   │
│                    │ Telegram     │   │
│                    └──────────────┘   │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Google Cloud    │ ← Enable APIs here!
│ Project 803...  │
└─────────────────┘
```

---

## ✅ After Everything Works

Your workflow will be:
1. Send Telegram message
2. Bot extracts F1 data
3. Bot creates Google Sheet
4. Bot shares sheet
5. Bot emails you the link
6. You receive email with sheet link ✉️

**Total time:** ~30 seconds per workflow

---

## 🔐 Security Note

The `credentials.json` file contains your Google Cloud service account key. 
- ✅ It's in `.gitignore` (won't be committed)
- ✅ Keep it secure
- ✅ Don't share it

---

**Ready? Start with Step 1 above! 🚀**

