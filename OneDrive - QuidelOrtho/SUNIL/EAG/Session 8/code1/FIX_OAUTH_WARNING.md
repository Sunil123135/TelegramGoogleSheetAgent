# Fix "Google hasn't verified this app" Warning

## Quick Fix (Recommended for Personal Use)

When you see the warning screen:

```
⚠️ Google hasn't verified this app
The app is requesting access to sensitive info...
```

**Steps to proceed:**
1. Click **"Advanced"** (small text at bottom left)
2. Click **"Go to Cursor Agent (unsafe)"** or **"Go to [Your App Name] (unsafe)"**
3. Review the permissions shown
4. Click **"Allow"**

✅ **This is safe** - it's your own application and you control the code.

---

## Permanent Solution: Add Yourself as Test User

To avoid seeing this warning every time:

### Step 1: Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### Step 2: Navigate to OAuth Consent Screen
1. Select your project
2. Go to **"APIs & Services"** → **"OAuth consent screen"**

### Step 3: Add Your Email as Test User
1. Scroll down to the **"Test users"** section
2. Click **"+ ADD USERS"**
3. Enter your email: **sunil.nitie@gmail.com**
4. Click **"Save"**

### Step 4: Verify Settings
Make sure:
- ✅ User Type: **External**
- ✅ Publishing status: **Testing** (not "In production")
- ✅ Test users: Your email is listed

### Step 5: Delete Old Token and Retry
```bash
# Delete the old token file
rm "C:\Users\slalwani\.config\cursor-agent\google\sheets_token.json"

# Run OAuth again
python test_oauth.py
```

---

## Understanding the Warning

### Why does this happen?
- Google requires apps to go through a verification process before they can be used publicly
- Apps in "Testing" mode can only be used by listed test users
- Apps in "Production" mode need Google's verification (takes weeks)

### Is it safe to bypass?
**YES**, if:
- ✅ It's your own app (you wrote the code)
- ✅ You trust the developer (that's you!)
- ✅ You're the only one using it

**NO**, if:
- ❌ Someone else sent you the app
- ❌ You don't know what permissions it's requesting
- ❌ The code is from an untrusted source

### For your case:
✅ **It's completely safe** - you created this app, you have the source code, and you're only accessing your own Google Sheets.

---

## Alternative: Publish Status Options

### Option 1: Stay in Testing (Recommended)
- **Pro**: No verification needed
- **Pro**: Works immediately
- **Con**: Need to add test users manually
- **Con**: Shows warning to users not in test list
- **Best for**: Personal projects, internal tools

### Option 2: Verify with Google
- **Pro**: No warning for any user
- **Pro**: Can be used by anyone
- **Con**: Takes 4-6 weeks
- **Con**: Requires domain verification
- **Con**: Requires privacy policy
- **Best for**: Public applications

For personal use, **stay in Testing mode** and add yourself as a test user.

---

## Current Setup

Your OAuth configuration:
```
App: Cursor Agent
Developer: sunil.nitie@gmail.com
Scopes: https://www.googleapis.com/auth/spreadsheets
Status: Testing (unverified)
```

This is **perfect for personal/development use**.

---

## Troubleshooting

### "Test user list is full"
- Testing mode allows up to 100 test users
- You only need yourself, so this shouldn't be an issue

### Warning still appears after adding test user
- Wait 5-10 minutes for changes to propagate
- Delete existing token: `sheets_token.json`
- Try OAuth flow again

### "Access blocked: This app's request is invalid"
- Check that Google Sheets API is enabled
- Verify the scope in OAuth consent screen matches the code
- Make sure `client_secret.json` is for the correct project

---

## Next Steps

1. ✅ Click "Advanced" → "Go to Cursor Agent (unsafe)" to proceed now
2. ✅ Add yourself as test user to avoid the warning in the future
3. ✅ Run `python test_oauth.py` to complete OAuth

The warning is normal and safe to bypass for your own apps!

