# F1 Bot Easy Startup Script
# This script opens two PowerShell windows:
# 1. SSE Servers
# 2. Telegram Bot

Write-Host "`n🏎️  Starting F1 Web Scraping Bot...`n" -ForegroundColor Cyan

$projectPath = "C:\Users\slalwani\OneDrive - QuidelOrtho\SUNIL\EAG\Session 8\code1"

# Check if .env exists
if (-not (Test-Path "$projectPath\.env")) {
    Write-Host "❌ ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "`nPlease run these commands first:" -ForegroundColor Yellow
    Write-Host "  Copy-Item env.example .env" -ForegroundColor Cyan
    Write-Host "  notepad .env" -ForegroundColor Cyan
    Write-Host "`nThen edit SELF_EMAIL, TELEGRAM_BOT_TOKEN, and TELEGRAM_CHAT_ID" -ForegroundColor Yellow
    Write-Host "`nPress any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check if credentials.json exists
if (-not (Test-Path "$projectPath\credentials.json")) {
    Write-Host "⚠️  WARNING: credentials.json not found!" -ForegroundColor Yellow
    Write-Host "Google API calls may fail without this file." -ForegroundColor Yellow
    Write-Host "`nPress any key to continue anyway, or Ctrl+C to cancel..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "✅ Configuration files found" -ForegroundColor Green
Write-Host "`n🚀 Opening two PowerShell windows..." -ForegroundColor Cyan
Write-Host "   1. SSE Servers (7 servers on ports 8001-8007)" -ForegroundColor White
Write-Host "   2. Telegram Bot Poller" -ForegroundColor White
Write-Host "`n⏳ Please wait 5-10 seconds for servers to start..." -ForegroundColor Yellow
Write-Host "`n📱 Once both windows show success:" -ForegroundColor Green
Write-Host "   • Open Telegram" -ForegroundColor White
Write-Host "   • Send 'f1' to your bot" -ForegroundColor Cyan
Write-Host "   • Get your Google Sheet!" -ForegroundColor White
Write-Host "`n🔴 DO NOT CLOSE the windows that open!" -ForegroundColor Red
Write-Host "`n============================================================`n" -ForegroundColor Gray

# Start SSE Servers in new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; Write-Host '`n🚀 Starting SSE Servers...' -ForegroundColor Cyan; python start_sse_servers.py"
)

# Wait 3 seconds for servers to initialize
Start-Sleep -Seconds 3

# Start Telegram Bot in new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; Write-Host '`n🤖 Starting Telegram Bot...' -ForegroundColor Cyan; python .cursor\telegram_poller.py"
)

Write-Host "✅ Startup script completed!" -ForegroundColor Green
Write-Host "`n📝 Check the two PowerShell windows for status." -ForegroundColor White
Write-Host "`nTo stop everything:" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C in both windows" -ForegroundColor Cyan
Write-Host "  OR run: Stop-Process -Name python -Force" -ForegroundColor Cyan
Write-Host "`n============================================================`n" -ForegroundColor Gray

Write-Host "Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

