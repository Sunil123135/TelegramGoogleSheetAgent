# Interactive Google API Enabler
# This script will open the API pages and wait for you to enable them

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "🔧 GOOGLE API ENABLER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n📋 Your Project ID: 803760333185`n" -ForegroundColor Yellow

Write-Host "This script will:" -ForegroundColor White
Write-Host "  1. Open 3 browser tabs (one for each API)" -ForegroundColor Gray
Write-Host "  2. Wait for you to click 'ENABLE' on each" -ForegroundColor Gray
Write-Host "  3. Restart all services automatically`n" -ForegroundColor Gray

$apis = @(
    @{Name="Google Sheets API"; URL="https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=803760333185"},
    @{Name="Google Drive API"; URL="https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=803760333185"},
    @{Name="Gmail API"; URL="https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=803760333185"}
)

Write-Host "Opening browser tabs for each API...`n" -ForegroundColor Yellow

foreach ($api in $apis) {
    Write-Host "📂 Opening: $($api.Name)" -ForegroundColor White
    Start-Process $api.URL
    Start-Sleep -Seconds 2
}

Write-Host "`n============================================================" -ForegroundColor Yellow
Write-Host "⚠️  ACTION REQUIRED" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "`nIn each browser tab that just opened:" -ForegroundColor White
Write-Host "  1️⃣  Look for the blue 'ENABLE' button" -ForegroundColor Gray
Write-Host "  2️⃣  Click it" -ForegroundColor Gray
Write-Host "  3️⃣  Wait for confirmation (5-10 seconds)" -ForegroundColor Gray
Write-Host "`nDo this for ALL 3 tabs!`n" -ForegroundColor White

Write-Host "============================================================`n" -ForegroundColor Yellow

# Wait for user confirmation
$response = Read-Host "Have you enabled all 3 APIs? (yes/no)"

if ($response -eq "yes" -or $response -eq "y") {
    Write-Host "`n✅ Great! Waiting 30 seconds for APIs to activate..." -ForegroundColor Green
    Start-Sleep -Seconds 30
    
    Write-Host "`n🔄 Restarting services...`n" -ForegroundColor Cyan
    
    # Stop any running processes
    Stop-Process -Name python -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Start SSE servers
    Write-Host "▶️  Starting SSE servers..." -ForegroundColor White
    Start-Process -FilePath "python" -ArgumentList "start_sse_servers.py" -NoNewWindow
    Start-Sleep -Seconds 10
    
    # Check health
    Write-Host "`n🏥 Checking server health...`n" -ForegroundColor White
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
            $null = Invoke-WebRequest -Uri "http://localhost:$($server.Port)/health" -TimeoutSec 3 -ErrorAction Stop
            Write-Host "  ✅ $($server.Name)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ $($server.Name)" -ForegroundColor Red
            $allHealthy = $false
        }
    }
    
    if ($allHealthy) {
        # Start Telegram bot
        Write-Host "`n▶️  Starting Telegram bot..." -ForegroundColor White
        Start-Process -FilePath "python" -ArgumentList ".cursor\telegram_poller.py" -NoNewWindow
        Start-Sleep -Seconds 2
        
        Write-Host "`n============================================================" -ForegroundColor Green
        Write-Host "✅ ALL SYSTEMS READY!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "`n📱 Test your bot:" -ForegroundColor Cyan
        Write-Host "   Send: Get F1 standings and create a sheet`n" -ForegroundColor Yellow
    } else {
        Write-Host "`n⚠️  Some servers failed. Check errors above.`n" -ForegroundColor Red
    }
    
} else {
    Write-Host "`n⚠️  Please enable the APIs first, then run this script again.`n" -ForegroundColor Yellow
}

