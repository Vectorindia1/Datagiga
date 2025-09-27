#!/usr/bin/env pwsh
Write-Host "🚀 Starting Local Gigasheet Clone..." -ForegroundColor Green

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

# Check if ports are available
if (Test-Port 8000) {
    Write-Host "❌ Port 8000 is already in use. Please stop any existing services." -ForegroundColor Red
    exit 1
}

if (Test-Port 3000) {
    Write-Host "❌ Port 3000 is already in use. Please stop any existing services." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Starting backend service..." -ForegroundColor Yellow
# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    py main.py
}

Write-Host "Backend started with Job ID: $($backendJob.Id)" -ForegroundColor Green

# Wait a moment for backend to start
Start-Sleep -Seconds 3

Write-Host "🎨 Starting frontend service..." -ForegroundColor Yellow
# Start frontend in background
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm start
}

Write-Host "Frontend started with Job ID: $($frontendJob.Id)" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Services started successfully!" -ForegroundColor Green
Write-Host "📊 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🎨 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📁 Data folder: $PWD\data (place your Excel files here)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Features available:" -ForegroundColor White
Write-Host "✅ Upload and process massive CSV files" -ForegroundColor Green
Write-Host "✅ Merge multiple Excel files" -ForegroundColor Green
Write-Host "✅ Real-time filtering and search" -ForegroundColor Green
Write-Host "✅ Handle 1 crore+ rows efficiently" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Function to clean up jobs
function Stop-Services {
    Write-Host "`n🛑 Stopping services..." -ForegroundColor Yellow
    
    # Stop jobs
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*react-scripts*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ All services stopped." -ForegroundColor Green
}

# Handle Ctrl+C
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Stop-Services
}

try {
    # Monitor jobs and wait
    while ($backendJob.State -eq "Running" -or $frontendJob.State -eq "Running") {
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed") {
            Write-Host "❌ Backend service failed!" -ForegroundColor Red
            Receive-Job $backendJob
            break
        }
        if ($frontendJob.State -eq "Failed") {
            Write-Host "❌ Frontend service failed!" -ForegroundColor Red
            Receive-Job $frontendJob
            break
        }
        
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "Service interrupted." -ForegroundColor Yellow
} finally {
    Stop-Services
}