#!/usr/bin/env pwsh
Write-Host "🚀 Starting GigaSheet Local Clone - Full Stack" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

# Ensure we're in the right directory
Set-Location $PSScriptRoot

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        return $connection
    } catch {
        return $false
    }
}

# Check if ports are available
Write-Host "🔍 Checking port availability..." -ForegroundColor Yellow

if (Test-Port 8000) {
    Write-Host "❌ Port 8000 (Backend) is already in use!" -ForegroundColor Red
    Write-Host "Please stop any existing services or use a different port." -ForegroundColor Yellow
    exit 1
}

if (Test-Port 3000) {
    Write-Host "❌ Port 3000 (Frontend) is already in use!" -ForegroundColor Red
    Write-Host "Please stop any existing services or use a different port." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Ports 8000 and 3000 are available" -ForegroundColor Green

# Start Backend
Write-Host ""
Write-Host "🔧 Starting Backend Server (FastAPI + DuckDB)..." -ForegroundColor Yellow
Write-Host "📍 Backend will be available at: http://localhost:8000" -ForegroundColor Gray

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    & .\.venv\Scripts\Activate.ps1
    python gigasheet-local\backend\main.py
}

if ($backendJob) {
    Write-Host "✅ Backend started successfully (Job ID: $($backendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start backend" -ForegroundColor Red
    exit 1
}

# Wait for backend to initialize
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test backend connection
$backendReady = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response) {
            $backendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if ($backendReady) {
    Write-Host "✅ Backend is responding and ready!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Backend may still be starting up..." -ForegroundColor Yellow
}

# Start Frontend
Write-Host ""
Write-Host "🎨 Starting Frontend Server (HTML + JavaScript)..." -ForegroundColor Yellow
Write-Host "📍 Frontend will be available at: http://localhost:3000" -ForegroundColor Gray

$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    & .\.venv\Scripts\Activate.ps1
    python frontend\server.py
}

if ($frontendJob) {
    Write-Host "✅ Frontend started successfully (Job ID: $($frontendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start frontend" -ForegroundColor Red
    # Stop backend if frontend fails
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    exit 1
}

# Wait for frontend to start
Write-Host "⏳ Waiting for frontend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Display success information
Write-Host ""
Write-Host "🎉 GigaSheet Local Clone is now running!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Backend API:     http://localhost:8000" -ForegroundColor Cyan
Write-Host "🎨 Frontend UI:     http://localhost:3000" -ForegroundColor Cyan
Write-Host "📖 API Docs:        http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "🗂️  Data Directory: $PSScriptRoot\gigasheet-local\data" -ForegroundColor Yellow
Write-Host "   (Place your Excel files here for merging)" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ Features Available:" -ForegroundColor White
Write-Host "   ✅ Upload massive CSV files (1 crore+ rows)" -ForegroundColor Green
Write-Host "   ✅ Merge multiple Excel files" -ForegroundColor Green
Write-Host "   ✅ Real-time data filtering and search" -ForegroundColor Green
Write-Host "   ✅ Persistent data storage with DuckDB" -ForegroundColor Green
Write-Host "   ✅ Export data in multiple formats" -ForegroundColor Green
Write-Host ""

# Open browser
Write-Host "🌐 Opening browser in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    Start-Process "http://localhost:3000"
    Write-Host "✅ Browser opened successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not open browser automatically." -ForegroundColor Yellow
    Write-Host "Please manually navigate to: http://localhost:3000" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🛑 Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Function to clean up services
function Stop-AllServices {
    Write-Host "`nStopping all services..." -ForegroundColor Yellow
    
    # Stop jobs
    if ($backendJob) {
        Write-Host "   Stopping backend..." -ForegroundColor Gray
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Write-Host "   Stopping frontend..." -ForegroundColor Gray
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*main.py*" -or $_.CommandLine -like "*server.py*" 
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ All services stopped." -ForegroundColor Green
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Stop-AllServices
}

# Monitor services and wait for user interruption
try {
    Write-Host "🔄 Monitoring services... (Backend Job: $($backendJob.Id), Frontend Job: $($frontendJob.Id))" -ForegroundColor Gray
    
    while ($true) {
        # Check if jobs are still running
        $backendState = Get-Job $backendJob.Id -ErrorAction SilentlyContinue | Select-Object -ExpandProperty State
        $frontendState = Get-Job $frontendJob.Id -ErrorAction SilentlyContinue | Select-Object -ExpandProperty State
        
        if ($backendState -eq "Failed") {
            Write-Host "❌ Backend service failed!" -ForegroundColor Red
            Write-Host "Backend output:" -ForegroundColor Yellow
            Receive-Job $backendJob
            break
        }
        if ($frontendState -eq "Failed") {
            Write-Host "❌ Frontend service failed!" -ForegroundColor Red
            Write-Host "Frontend output:" -ForegroundColor Yellow
            Receive-Job $frontendJob
            break
        }
        
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "`nServices interrupted by user." -ForegroundColor Yellow
} finally {
    Stop-AllServices
}