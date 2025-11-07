# Stop All F1 Bot Services
# This script stops all Python processes (SSE servers and Telegram bot)

Write-Host "`n🛑 Stopping F1 Bot Services...`n" -ForegroundColor Yellow

# Check if any Python processes are running
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue

if ($null -eq $pythonProcesses) {
    Write-Host "✅ No Python processes found running." -ForegroundColor Green
    Write-Host "`nNothing to stop!" -ForegroundColor White
} else {
    Write-Host "Found $($pythonProcesses.Count) Python process(es) running:" -ForegroundColor Cyan
    $pythonProcesses | ForEach-Object {
        Write-Host "  PID: $($_.Id)" -ForegroundColor White
    }
    
    Write-Host "`n🔴 Stopping all Python processes..." -ForegroundColor Red
    Stop-Process -Name python -Force
    
    Write-Host "✅ All Python processes stopped!" -ForegroundColor Green
    Write-Host "`nServices stopped:" -ForegroundColor White
    Write-Host "  • SSE Servers (ports 8001-8007)" -ForegroundColor Gray
    Write-Host "  • Telegram Bot Poller" -ForegroundColor Gray
}

Write-Host "`nTo restart, run:" -ForegroundColor Yellow
Write-Host "  .\start_f1_bot.ps1" -ForegroundColor Cyan
Write-Host "`n============================================================`n" -ForegroundColor Gray

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

