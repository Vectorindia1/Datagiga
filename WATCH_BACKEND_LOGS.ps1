#!/usr/bin/env pwsh
# Watch Backend Logs in Real-Time

Write-Host "`n╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      BACKEND LOG MONITOR (LIVE VIEW)      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Monitoring backend logs..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

# Find the running backend job
$backendJob = Get-Job | Where-Object { $_.Command -like '*backend*' -and $_.State -eq 'Running' } | Select-Object -First 1

if (-not $backendJob) {
    Write-Host "❌ Backend job not found!" -ForegroundColor Red
    Write-Host "Make sure backend is running with:`n  Start-Job ..." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Monitoring Job ID: $($backendJob.Id)" -ForegroundColor Green
Write-Host "  Backend is running at http://localhost:8000`n" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor DarkGray

$lastCount = 0

while ($true) {
    $logs = Receive-Job -Id $backendJob.Id -Keep
    $currentCount = $logs.Count
    
    if ($currentCount -gt $lastCount) {
        # New log entries
        $newLogs = $logs[$lastCount..($currentCount-1)]
        
        foreach ($log in $newLogs) {
            $logStr = $log.ToString()
            
            # Color code different log types
            if ($logStr -match '\[UPLOAD\]') {
                Write-Host $logStr -ForegroundColor Cyan
            }
            elseif ($logStr -match '\[PROCESSING\]') {
                Write-Host $logStr -ForegroundColor Yellow
            }
            elseif ($logStr -match '\[EXCEL\]') {
                Write-Host $logStr -ForegroundColor Magenta
            }
            elseif ($logStr -match '\[SUCCESS\]') {
                Write-Host $logStr -ForegroundColor Green
            }
            elseif ($logStr -match '\[ERROR\]') {
                Write-Host $logStr -ForegroundColor Red
            }
            elseif ($logStr -match 'INFO:') {
                # Skip INFO logs unless they're important
                if ($logStr -match 'POST|GET /tables') {
                    # Skip routine API calls
                }
                else {
                    Write-Host $logStr -ForegroundColor DarkGray
                }
            }
            else {
                Write-Host $logStr
            }
        }
        
        $lastCount = $currentCount
    }
    
    Start-Sleep -Milliseconds 500
}
