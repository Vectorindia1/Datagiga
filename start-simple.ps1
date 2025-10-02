Write-Host "Starting GigaSheet Local Clone - Full Stack" -ForegroundColor Green

# Ensure we're in the right directory
Set-Location $PSScriptRoot

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Start Backend in background
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    & .\.venv\Scripts\Activate.ps1
    python gigasheet-local\backend\main.py
}

Write-Host "Backend started (Job ID: $($backendJob.Id))" -ForegroundColor Green

# Wait a moment for backend to start
Start-Sleep -Seconds 5

# Start Frontend in background
Write-Host "Starting Frontend Server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    & .\.venv\Scripts\Activate.ps1
    python frontend\server.py
}

Write-Host "Frontend started (Job ID: $($frontendJob.Id))" -ForegroundColor Green

# Wait for frontend to start
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "GigaSheet Local Clone is now running!" -ForegroundColor Green
Write-Host "Backend API:     http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend UI:     http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Docs:        http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Open browser
Write-Host "Opening browser..." -ForegroundColor Yellow
try {
    Start-Process "http://localhost:3000"
    Write-Host "Browser opened successfully!" -ForegroundColor Green
} catch {
    Write-Host "Could not open browser automatically." -ForegroundColor Yellow
    Write-Host "Please manually navigate to: http://localhost:3000" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Function to clean up services
function Stop-AllServices {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    
    # Stop jobs
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    Write-Host "All services stopped." -ForegroundColor Green
}

# Monitor services
try {
    while ($true) {
        $backendState = Get-Job $backendJob.Id -ErrorAction SilentlyContinue | Select-Object -ExpandProperty State
        $frontendState = Get-Job $frontendJob.Id -ErrorAction SilentlyContinue | Select-Object -ExpandProperty State
        
        if ($backendState -eq "Failed") {
            Write-Host "Backend service failed!" -ForegroundColor Red
            Receive-Job $backendJob
            break
        }
        if ($frontendState -eq "Failed") {
            Write-Host "Frontend service failed!" -ForegroundColor Red
            Receive-Job $frontendJob
            break
        }
        
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "Services interrupted by user." -ForegroundColor Yellow
} finally {
    Stop-AllServices
}