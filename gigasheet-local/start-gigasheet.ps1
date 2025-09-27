#!/usr/bin/env pwsh

Write-Host "Starting Local Gigasheet Clone with your 1 crore+ rows!" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = py --version 2>$null
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = npm --version 2>$null
    Write-Host "✅ Node.js/NPM found: v$nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js/NPM not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 Your Excel files detected:" -ForegroundColor Cyan
Get-ChildItem -Path "data\*.xlsx" | ForEach-Object {
    $sizeInMB = [math]::Round($_.Length / 1MB, 1)
    Write-Host "  📋 $($_.Name) ($sizeInMB MB)" -ForegroundColor Yellow
}

$excelCount = (Get-ChildItem -Path "data\*.xlsx").Count
Write-Host ""
Write-Host "📈 Total: $excelCount Excel files ready for processing!" -ForegroundColor Green
Write-Host ""

# Start Backend
Write-Host "🔧 Starting FastAPI backend server..." -ForegroundColor Yellow
Write-Host "   Backend will run at: http://localhost:8000" -ForegroundColor Gray

$backendProcess = Start-Process -PassThru -WindowStyle Normal -FilePath "py" -ArgumentList "main.py" -WorkingDirectory "$PWD\backend"

if ($backendProcess) {
    Write-Host "✅ Backend started (PID: $($backendProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start backend" -ForegroundColor Red
    exit 1
}

# Wait for backend to initialize
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Test backend connectivity
$backendReady = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/tables" -Method Get -TimeoutSec 3
        $backendReady = $true
        break
    } catch {
        Write-Host "   Attempt $i/5: Backend not ready yet..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
    }
}

if ($backendReady) {
    Write-Host "✅ Backend is ready and responding!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Backend may still be starting. Check the backend window." -ForegroundColor Yellow
}

# Start Frontend
Write-Host ""
Write-Host "🎨 Starting React frontend..." -ForegroundColor Yellow
Write-Host "   Frontend will run at: http://localhost:3000" -ForegroundColor Gray

$frontendProcess = Start-Process -PassThru -WindowStyle Normal -FilePath "npm" -ArgumentList "start" -WorkingDirectory "$PWD\frontend"

if ($frontendProcess) {
    Write-Host "✅ Frontend started (PID: $($frontendProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start frontend" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 GigaSheet Local is starting up!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access your application:" -ForegroundColor White
Write-Host "   🌐 Frontend UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 To process your 1 crore+ rows:" -ForegroundColor White
Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor Gray
Write-Host "   2. Click 'Merge Excel Files' button" -ForegroundColor Gray
Write-Host "   3. Wait for processing (may take 5-10 minutes)" -ForegroundColor Gray
Write-Host "   4. Explore your massive dataset with instant filtering!" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor White
Write-Host "   • Processing 10 large Excel files will take time" -ForegroundColor Gray
Write-Host "   • DuckDB is optimized for this exact use case" -ForegroundColor Gray
Write-Host "   • You'll get toast notifications when processing is done" -ForegroundColor Gray
Write-Host "   • The UI will remain responsive during processing" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "   Close both terminal windows or press Ctrl+C in each" -ForegroundColor Gray
Write-Host ""

# Wait for user input
Write-Host "Press any key to open the browser or close this window to continue..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open browser
try {
    Start-Process "http://localhost:3000"
    Write-Host "🌐 Opening browser..." -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not auto-open browser. Please manually navigate to http://localhost:3000" -ForegroundColor Yellow
}