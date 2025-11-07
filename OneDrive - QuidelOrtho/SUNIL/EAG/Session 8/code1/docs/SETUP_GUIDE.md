# Complete Setup Guide

Step-by-step instructions to get your Cursor Agent up and running.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher
- [ ] Git installed
- [ ] Google Account (for Google APIs)
- [ ] Telegram account (optional, for notifications)
- [ ] Gemini API key (get from [ai.google.dev](https://ai.google.dev))

---

## Step 1: Python Environment Setup

### Using uv (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd <your-workspace>
uv pip install -e .
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e .
```

---

## Step 2: Google Cloud Setup

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project"
3. Name it (e.g., "cursor-agent")
4. Click "Create"

### 2.2 Enable Required APIs

In your project, enable these APIs:

1. **Google Drive API**
   - Search for "Google Drive API"
   - Click "Enable"

2. **Google Sheets API**
   - Search for "Google Sheets API"
   - Click "Enable"

3. **Gmail API**
   - Search for "Gmail API"
   - Click "Enable"

### 2.3 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: "Cursor Agent"
   - User support email: your email
   - Developer contact: your email
   - Add scopes:
     - `.../auth/drive.file`
     - `.../auth/spreadsheets`
     - `.../auth/gmail.send`
   - Add test users: your email
   - Click "Save and Continue"

4. Back to "Create OAuth client ID":
   - Application type: Desktop app
   - Name: "Cursor Agent Desktop"
   - Click "Create"

5. Download the JSON file:
   - Click the download icon next to your credential
   - Save as `client_secret.json`

### 2.4 Place Credentials

```bash
# Create directory
mkdir -p ~/.config/cursor-agent/google

# Move the downloaded file
mv ~/Downloads/client_secret_*.json ~/.config/cursor-agent/google/client_secret.json

# Secure it
chmod 600 ~/.config/cursor-agent/google/client_secret.json
```

**Windows:**
```powershell
# Create directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\cursor-agent\google"

# Move the file
Move-Item "$env:USERPROFILE\Downloads\client_secret_*.json" "$env:USERPROFILE\.config\cursor-agent\google\client_secret.json"
```

---

## Step 3: Telegram Setup (Optional)

### 3.1 Create a Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow prompts:
   - Bot name: "Cursor Agent Bot"
   - Username: "cursor_agent_<yourname>_bot"
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3.2 Get Your Chat ID

1. Search for [@getidsbot](https://t.me/getidsbot) on Telegram
2. Send `/start`
3. Copy your chat ID (looks like `123456789`)

**Alternative method:**
```bash
# Message your bot first, then run:
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates

# Look for "chat":{"id":123456789}
```

---

## Step 4: Environment Configuration

### 4.1 Copy Example Config

```bash
cp env.example .env
```

### 4.2 Edit .env

```bash
# Open in your editor
nano .env
# or
code .env
```

### 4.3 Fill in Values

```bash
# Google APIs
GOOGLE_CLIENT_SECRET_PATH=~/.config/cursor-agent/google/client_secret.json
GOOGLE_DRIVE_TOKEN_PATH=~/.config/cursor-agent/google/drive_token.json
GOOGLE_SHEETS_TOKEN_PATH=~/.config/cursor-agent/google/sheets_token.json
GOOGLE_GMAIL_TOKEN_PATH=~/.config/cursor-agent/google/gmail_token.json

# Telegram (paste your values)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# SSE Server (generate a random token)
MCP_SSE_TOKEN=$(openssl rand -hex 32)

# Your email
SELF_EMAIL=your.email@gmail.com

# F1 standings URL (or any other data source)
F1_STANDINGS_URL=https://www.formula1.com/en/results.html/2025/drivers.html

# F1 output Google Sheet (optional - pre-configured output destination)
F1_OUTPUT_SHEET_URL=https://docs.google.com/spreadsheets/d/1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY/edit?usp=drive_link
F1_OUTPUT_SHEET_ID=1ptYH6IDLfHOKRXYAGh4ePT2M8IXRb1bW235ODWjQ_wY

# Model configuration (defaults are fine)
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5
GEMMA_MODEL=gemma3:12b
CHUNK_SIZE=512

# Paths (defaults are fine)
FAISS_INDEX_PATH=./data/faiss_index
MEMORY_SCRATCHPAD_PATH=./data/memory_scratchpad.jsonl
```

**Windows users**: Use Windows paths:
```bash
GOOGLE_CLIENT_SECRET_PATH=C:\Users\YourName\.config\cursor-agent\google\client_secret.json
```

---

## Step 5: Playwright Setup (for Screenshots)

```bash
# Install Playwright browsers
playwright install chromium

# If you get dependency errors (Linux):
playwright install-deps chromium
```

**Windows**: Chromium should install without issues.

---

## Step 6: First Run - OAuth Authorization

### 6.1 Run a Simple Test

```bash
python main.py interactive
```

### 6.2 OAuth Flow

On first run, a browser window will open for each Google API:

1. **Google Sheets OAuth**
   - Select your Google account
   - Review permissions
   - Click "Allow"
   - You can close the browser

2. **Google Drive OAuth**
   - Same process
   - Click "Allow"

3. **Gmail OAuth**
   - Same process
   - Click "Allow"

Tokens are saved to `~/.config/cursor-agent/google/*_token.json` for future use.

---

## Step 7: Verify Setup

### 7.1 Check Credentials

```bash
ls -la ~/.config/cursor-agent/google/

# Should show:
# client_secret.json
# drive_token.json (after first run)
# sheets_token.json (after first run)
# gmail_token.json (after first run)
```

### 7.2 Test Agent

```bash
python main.py f1
```

You should see:
```
============================================================
Cursor Agent - F1 Standings Workflow
============================================================

🎯 Goal: Find the Current Point Standings...

[MOCK] Created Google Sheet: F1_Current_Standings
...
```

If you see this, setup is complete! 🎉

---

## Step 8: Configure Cursor

### 8.1 Verify MCP Configuration

Check that `.cursor/mcp.json` exists and contains your MCP servers.

### 8.2 Restart Cursor

Close and reopen Cursor for MCP configuration to take effect.

---

## Common Issues

### Issue: "Client secret file not found"

**Solution:**
```bash
# Verify file exists
ls ~/.config/cursor-agent/google/client_secret.json

# Check .env path matches
cat .env | grep GOOGLE_CLIENT_SECRET_PATH
```

### Issue: "Invalid client secret"

**Solution:**
1. Download fresh credentials from Google Cloud Console
2. Ensure you selected "Desktop app" not "Web application"
3. Replace the old `client_secret.json`

### Issue: "Insufficient permissions"

**Solution:**
1. Go to Google Cloud Console → "OAuth consent screen"
2. Add your email to "Test users"
3. Check scopes include:
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/gmail.send`

### Issue: "Module not found" errors

**Solution:**
```bash
# Reinstall dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

### Issue: Playwright timeout

**Solution:**
```bash
# Increase timeout in code (agent/action/executor.py)
page.set_default_timeout(60000)  # 60 seconds

# Or install dependencies
playwright install-deps
```

### Issue: FAISS installation fails

**Solution:**
```bash
# Try CPU-only version
pip uninstall faiss-cpu faiss-gpu
pip install faiss-cpu
```

---

## Security Best Practices

### 1. Secure Credentials

```bash
# Set restrictive permissions
chmod 600 ~/.config/cursor-agent/google/*
chmod 600 .env
```

### 2. Add to .gitignore

```bash
echo ".env" >> .gitignore
echo "*.json" >> .gitignore
echo "data/" >> .gitignore
```

### 3. Use Environment-Specific Configs

```bash
# Development
cp .env .env.development

# Production
cp .env .env.production

# Load specific env
export ENV_FILE=.env.production
```

### 4. Rotate Tokens

```bash
# Delete tokens to force re-auth
rm ~/.config/cursor-agent/google/*_token.json

# Revoke access in Google Account settings
# Visit: https://myaccount.google.com/permissions
```

---

## Next Steps

Now that setup is complete:

1. ✅ **Run the F1 Workflow**
   ```bash
   python main.py f1
   ```

2. ✅ **Try Interactive Mode**
   ```bash
   python main.py interactive
   ```

3. ✅ **Read the Documentation**
   - [F1_WORKFLOW.md](./F1_WORKFLOW.md) - Detailed workflow walkthrough
   - [README.md](../README.md) - Complete feature documentation

4. ✅ **Build Your Own Workflows**
   - See examples in `main.py`
   - Add custom MCP servers
   - Extend the tool catalog

---

## Troubleshooting Help

If you're still having issues:

1. **Check Logs**
   ```bash
   # Run with verbose output
   python main.py f1 2>&1 | tee setup.log
   ```

2. **Verify Python Version**
   ```bash
   python --version  # Should be 3.11+
   ```

3. **Test Dependencies**
   ```bash
   python -c "import trafilatura; import pymupdf4llm; import faiss; import sentence_transformers; print('OK')"
   ```

4. **Check Disk Space**
   ```bash
   df -h  # Ensure sufficient space for models
   ```

---

**Setup Complete!** 🚀

You're ready to use the Cursor Agent. Happy coding!

