# Restart Services After Enabling Google APIs
# Run this script after enabling the Google Sheets, Drive, and Gmail APIs

Write-Host "`n🔄 Restarting Services..." -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

# Stop all Python processes
Write-Host "1️⃣  Stopping all Python processes..." -ForegroundColor White
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✅ Stopped`n" -ForegroundColor Green

# Start SSE servers
Write-Host "2️⃣  Starting SSE servers..." -ForegroundColor White
Start-Process -FilePath "python" -ArgumentList "start_sse_servers.py" -NoNewWindow
Write-Host "   ⏳ Waiting for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check server health
Write-Host "`n3️⃣  Checking server health..." -ForegroundColor White
$servers = @(
    @{Name="Trafilatura"; Port=8001},
    @{Name="MuPDF4LLM"; Port=8002},
    @{Name="Gemma"; Port=8003},
    @{Name="Google Sheets"; Port=8004},
    @{Name="Google Drive"; Port=8005},
    @{Name="Gmail"; Port=8006},
    @{Name="Telegram"; Port=8007}
)

$allHealthy = $true
foreach ($server in $servers) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($server.Port)/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   ✅ $($server.Name)" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ $($server.Name)" -ForegroundColor Red
        $allHealthy = $false
    }
}

if ($allHealthy) {
    Write-Host "`n4️⃣  Starting Telegram Bot..." -ForegroundColor White
    Start-Process -FilePath "python" -ArgumentList ".cursor\telegram_poller.py" -NoNewWindow
    Start-Sleep -Seconds 2
    Write-Host "   ✅ Telegram bot started`n" -ForegroundColor Green
    
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ ALL SERVICES RUNNING!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "`n📱 Test your bot with:" -ForegroundColor Cyan
    Write-Host "   'Get F1 standings and create a sheet'" -ForegroundColor Yellow
    Write-Host "`n============================================================`n" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some servers failed to start" -ForegroundColor Red
    Write-Host "   Check the errors above and try again`n" -ForegroundColor Yellow
}

