#!/usr/bin/env pwsh

Write-Host "🚀 Starting Local Gigasheet Clone..." -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>$null
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 Starting Backend (FastAPI + DuckDB)..." -ForegroundColor Yellow
Write-Host "   Backend URL: http://localhost:8000" -ForegroundColor Gray

# Start Backend in new window
$backendPath = Join-Path $PWD "backend"
Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory $backendPath -WindowStyle Normal

Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Test backend
Write-Host "🔍 Testing backend connection..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/tables" -Method Get -TimeoutSec 3
        $backendReady = $true
        Write-Host "✅ Backend is ready!" -ForegroundColor Green
        break
    } catch {
        Write-Host "   Attempt $i/5: Backend starting..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $backendReady) {
    Write-Host "⚠️  Backend may still be starting. Check the backend window." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎨 Starting Frontend (React + AG Grid)..." -ForegroundColor Yellow
Write-Host "   Frontend URL: http://localhost:3000" -ForegroundColor Gray

# Start Frontend in new window
$frontendPath = Join-Path $PWD "frontend"
Start-Process -FilePath "npm" -ArgumentList "start" -WorkingDirectory $frontendPath -WindowStyle Normal

Write-Host ""
Write-Host "🎉 System is starting up!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access your application:" -ForegroundColor White
Write-Host "   🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 To process your Excel files:" -ForegroundColor White
Write-Host "   1. Open http://localhost:3000" -ForegroundColor Gray
Write-Host "   2. Click 'Smart Incremental Merge'" -ForegroundColor Gray
Write-Host "   3. Wait for processing" -ForegroundColor Gray
Write-Host "   4. Explore your data!" -ForegroundColor Gray
Write-Host ""

# Wait and open browser
Write-Host "Press any key to open the browser..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

try {
    Start-Process "http://localhost:3000"
    Write-Host "🌐 Opening browser..." -ForegroundColor Green
} catch {
    Write-Host "Could not open browser. Please go to: http://localhost:3000" -ForegroundColor Yellow
}
