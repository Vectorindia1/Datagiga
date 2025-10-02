#!/usr/bin/env pwsh
# Data Studio - Quick Start Script
# Starts both backend and frontend servers

Write-Host "🚀 Starting Data Studio..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python found" -ForegroundColor Green

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
    return $connection
}

# Check if backend is already running
if (Test-Port 8000) {
    Write-Host "⚠️  Backend already running on port 8000" -ForegroundColor Yellow
    $restart = Read-Host "Do you want to restart it? (y/N)"
    if ($restart -eq 'y' -or $restart -eq 'Y') {
        Write-Host "Stopping existing backend..."
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Check if frontend is already running
if (Test-Port 3000) {
    Write-Host "⚠️  Frontend already running on port 3000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📂 Project Directory: $PSScriptRoot" -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "🔧 Starting Backend Server..." -ForegroundColor Cyan
$backendPath = Join-Path $PSScriptRoot "gigasheet-local\backend"

if (Test-Path $backendPath) {
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host '🔧 Backend Server' -ForegroundColor Green; python main.py"
    Write-Host "✅ Backend started on http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "❌ Backend directory not found: $backendPath" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "🎨 Starting Frontend Server..." -ForegroundColor Cyan
$frontendPath = Join-Path $PSScriptRoot "frontend"

if (Test-Path $frontendPath) {
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host '🎨 Frontend Server' -ForegroundColor Cyan; python server.py"
    Write-Host "✅ Frontend started on http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend directory not found: $frontendPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "🎉 Data Studio is now running!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "📱 Frontend:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend:   " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   • Drag & drop files to upload" -ForegroundColor DarkGray
Write-Host "   • Use tabs to navigate between Upload, Browse, and Analyze" -ForegroundColor DarkGray
Write-Host "   • Place Excel files in gigasheet-local/data/ for merging" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press Ctrl+C in the server windows to stop" -ForegroundColor DarkGray
Write-Host ""

# Wait for user input
Read-Host "Press Enter to exit this window"
