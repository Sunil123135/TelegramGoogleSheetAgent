# Quick Restart Script
# Run this AFTER enabling the Google APIs

Write-Host "`n🔄 Restarting All Services..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Stop all Python processes
Write-Host "1️⃣  Stopping services..." -ForegroundColor White
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Write-Host "   ✅ Stopped`n" -ForegroundColor Green

# Start SSE servers
Write-Host "2️⃣  Starting SSE servers..." -ForegroundColor White
Start-Process -FilePath "python" -ArgumentList "start_sse_servers.py" -NoNewWindow
Write-Host "   ⏳ Initializing..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check health
Write-Host "`n3️⃣  Health check..." -ForegroundColor White
$servers = @(8001, 8002, 8003, 8004, 8005, 8006, 8007)
$names = @("Trafilatura", "MuPDF4LLM", "Gemma", "Sheets", "Drive", "Gmail", "Telegram")
$allHealthy = $true

for ($i = 0; $i -lt $servers.Length; $i++) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:$($servers[$i])/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   ✅ $($names[$i])" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ $($names[$i])" -ForegroundColor Red
        $allHealthy = $false
    }
}

if ($allHealthy) {
    # Start Telegram bot
    Write-Host "`n4️⃣  Starting Telegram bot..." -ForegroundColor White
    Start-Process -FilePath "python" -ArgumentList ".cursor\telegram_poller.py" -NoNewWindow
    Start-Sleep -Seconds 2
    Write-Host "   ✅ Started`n" -ForegroundColor Green
    
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ ALL SERVICES RUNNING!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "`n📱 Test your Telegram bot now!" -ForegroundColor Cyan
    Write-Host "   Message: Get F1 standings and create a sheet`n" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Some services failed to start" -ForegroundColor Red
    Write-Host "   This usually means APIs are not enabled yet.`n" -ForegroundColor Yellow
    Write-Host "💡 Make sure you:" -ForegroundColor Cyan
    Write-Host "   1. Enabled all 3 APIs in Google Console" -ForegroundColor White
    Write-Host "   2. Waited 1-2 minutes after enabling" -ForegroundColor White
    Write-Host "   3. Try running this script again`n" -ForegroundColor White
}

